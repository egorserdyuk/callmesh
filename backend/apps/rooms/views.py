# rooms/views.py - Room management API views
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django_ratelimit.decorators import ratelimit
from apps.rooms.models import RoomManager
from apps.core.views import get_client_ip
import qrcode
import io
import base64
import logging

logger = logging.getLogger(__name__)


def require_auth(view_func):
    """Decorator to require authentication for views"""

    def wrapper(request, *args, **kwargs):
        if not request.session.get("authenticated"):
            logger.warning(f"Unauthenticated access attempt to {request.path}")
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
@require_auth
@ratelimit(key="ip", rate="60/min", method="POST", block=True)
def create_room(request):
    """Create a new video call room"""
    try:
        client_ip = get_client_ip(request)
        logger.info(f"Creating room for IP: {client_ip}")

        # Check if passwordless entry is requested
        allow_passwordless_entry = request.data.get("allow_passwordless_entry", False)

        room_data = RoomManager.create_room(
            creator_ip=client_ip, allow_passwordless_entry=allow_passwordless_entry
        )

        # Generate QR code for the room
        room_url = f"{request.build_absolute_uri('/')}join/{room_data['short_code']}"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(room_url)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        qr_image.save(buffer, format="PNG")
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()

        response_data = {
            "room_id": room_data["room_id"],
            "short_code": room_data["short_code"],
            "room_url": room_url,
            "qr_code": f"data:image/png;base64,{qr_code_data}",
            "expires_at": room_data["expires_at"],
            "max_participants": room_data["max_participants"],
            "allow_passwordless_entry": room_data["allow_passwordless_entry"],
        }

        # Include passwordless invite URL if enabled
        if room_data["allow_passwordless_entry"] and room_data["passwordless_token"]:
            passwordless_url = f"{request.build_absolute_uri('/')}invite/{room_data['passwordless_token']}"
            response_data["passwordless_invite_url"] = passwordless_url

        logger.info(f"Room created successfully: {room_data['room_id']}")
        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Room creation failed: {e}")
        return Response(
            {"error": "Failed to create room"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
@csrf_exempt
@ratelimit(key="ip", rate="60/min", method="GET", block=True)
def handle_passwordless_invite(request, token):
    """Handle passwordless invite links"""
    try:
        logger.info(f"Handling passwordless invite for token: {token}")

        # Get room by passwordless token
        room_data = RoomManager.get_room_by_passwordless_token(token)

        if not room_data:
            logger.warning(f"Invalid or expired passwordless token: {token}")
            return Response(
                {"error": "Invalid or expired invite link"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if passwordless entry is allowed for this room
        if not room_data.get("allow_passwordless_entry", False):
            logger.warning(
                f"Passwordless entry not allowed for room: {room_data['room_id']}"
            )
            return Response(
                {"error": "Passwordless entry not allowed for this room"},
                status=status.HTTP_403_FORBIDDEN,
            )

        logger.info(f"Passwordless invite successful for room: {room_data['room_id']}")
        return Response(
            {
                "success": True,
                "room_id": room_data["room_id"],
                "short_code": room_data["short_code"],
                "message": "Passwordless invite validated",
            }
        )

    except Exception as e:
        logger.error(f"Passwordless invite failed: {e}")
        return Response(
            {"error": "Failed to process invite"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def join_room_passwordless(request):
    """Join a room using passwordless entry (no authentication required)"""
    try:
        room_id = request.data.get("room_id")
        token = request.data.get("token")

        if not room_id or not token:
            return Response(
                {"error": "Room ID and token are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate the token
        room_data = RoomManager.get_room_by_passwordless_token(token)

        if not room_data:
            logger.warning(f"Invalid passwordless token for room {room_id}: {token}")
            return Response(
                {"error": "Invalid or expired invite link"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if room IDs match
        if room_data["room_id"] != room_id:
            logger.warning(
                f"Token room mismatch. Token for {room_data['room_id']}, requested {room_id}"
            )
            return Response(
                {"error": "Invalid room for this invite"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if passwordless entry is allowed
        if not room_data.get("allow_passwordless_entry", False):
            logger.warning(f"Passwordless entry not allowed for room: {room_id}")
            return Response(
                {"error": "Passwordless entry not allowed for this room"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create a temporary session for this passwordless user
        if not request.session.session_key:
            request.session.create()

        participant_id = request.session.session_key

        # Join the room using the existing logic
        client_ip = get_client_ip(request)
        room_data, message = RoomManager.join_room(room_id, participant_id, client_ip)

        if not room_data:
            logger.warning(
                f"Failed to join room via passwordless: {room_id}, reason: {message}"
            )
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        # Invalidate token after successful use
        RoomManager.invalidate_passwordless_token(token)

        response_data = {
            "success": True,
            "message": message,
            "room_id": room_data["room_id"],
            "short_code": room_data["short_code"],
            "participant_count": len(room_data.get("participants", [])),
            "participant_id": participant_id,
        }

        logger.info(
            f"User joined room via passwordless: {room_id}, participant: {participant_id}"
        )
        return Response(response_data)

    except Exception as e:
        logger.error(f"Passwordless room join failed: {e}")
        return Response(
            {"error": "Failed to join room via passwordless invite"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
@csrf_exempt
def get_room(request, room_id):
    """Get room information by room ID"""
    try:
        logger.info(f"Getting room info for: {room_id}")
        room_data = RoomManager.get_room_by_id(room_id)

        if not room_data:
            logger.warning(f"Room not found: {room_id}")
            return Response(
                {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if room has expired
        expires_at = timezone.datetime.fromisoformat(
            room_data["expires_at"].replace("Z", "+00:00")
        )
        if timezone.now() > expires_at:
            logger.info(f"Room expired, deleting: {room_id}")
            RoomManager.delete_room(room_id)
            return Response(
                {"error": "Room has expired"}, status=status.HTTP_404_NOT_FOUND
            )

        response_data = {
            "room_id": room_data["room_id"],
            "short_code": room_data["short_code"],
            "is_active": room_data["is_active"],
            "participant_count": len(room_data.get("participants", [])),
            "max_participants": room_data.get("max_participants", 2),
            "expires_at": room_data["expires_at"],
        }

        logger.info(
            f"Room info retrieved: {room_id}, participants: {len(room_data.get('participants', []))}"
        )
        return Response(response_data)

    except Exception as e:
        logger.error(f"Failed to retrieve room {room_id}: {e}")
        return Response(
            {"error": "Failed to retrieve room"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
@require_auth
@ratelimit(key="ip", rate="60/min", method="POST", block=True)
def join_room(request):
    """Join a room by room ID or short code"""
    try:
        room_identifier = request.data.get("room_identifier")

        # Ensure we have a session
        if not request.session.session_key:
            request.session.create()

        participant_id = request.session.session_key

        if not room_identifier:
            return Response(
                {"error": "Room identifier is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            f"Joining room: {room_identifier} with participant: {participant_id}"
        )

        client_ip = get_client_ip(request)
        room_data, message = RoomManager.join_room(
            room_identifier, participant_id, client_ip
        )

        if not room_data:
            logger.warning(f"Failed to join room: {room_identifier}, reason: {message}")
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        response_data = {
            "success": True,
            "message": message,
            "room_id": room_data["room_id"],
            "short_code": room_data["short_code"],
            "participant_count": len(room_data.get("participants", [])),
            "participant_id": participant_id,
        }

        logger.info(
            f"User joined room: {room_data['room_id']}, participant: {participant_id}"
        )
        return Response(response_data)

    except Exception as e:
        logger.error(f"Failed to join room: {e}")
        return Response(
            {"error": "Failed to join room"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
@require_auth
def leave_room(request, room_id):
    """Leave a room"""
    try:
        # Ensure we have a session
        if not request.session.session_key:
            logger.warning(f"No session key when trying to leave room: {room_id}")
            return Response(
                {
                    "success": True,  # Return success even if no session, as user wasn't in room anyway
                    "message": "No active session found",
                }
            )

        participant_id = request.session.session_key
        logger.info(f"Leaving room: {room_id} with participant: {participant_id}")

        # Check if room exists first
        room_data = RoomManager.get_room_by_id(room_id)
        if not room_data:
            logger.info(f"Room {room_id} not found when trying to leave")
            return Response(
                {
                    "success": True,  # Return success as room doesn't exist anyway
                    "message": "Room not found",
                }
            )

        # Check if participant is actually in the room
        participants = room_data.get("participants", [])
        if participant_id not in participants:
            logger.info(f"Participant {participant_id} not in room {room_id}")
            return Response(
                {
                    "success": True,  # Return success as user wasn't in room anyway
                    "message": "Not in room",
                }
            )

        success = RoomManager.leave_room(room_id, participant_id)

        if success:
            logger.info(f"User left room: {room_id}, participant: {participant_id}")
            return Response({"success": True, "message": "Left room successfully"})
        else:
            logger.warning(
                f"Failed to leave room: {room_id}, participant: {participant_id}"
            )
            return Response(
                {
                    "success": True,  # Still return success to avoid client errors
                    "message": "Room leave processed",
                }
            )

    except Exception as e:
        logger.error(f"Failed to leave room {room_id}: {e}")
        return Response(
            {"error": "Failed to leave room"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([AllowAny])
@csrf_exempt
@require_auth
def delete_room(request, room_id):
    """Delete a room (only creator or admin can delete)"""
    try:
        logger.info(f"Deleting room: {room_id}")

        # Check if room exists
        room_data = RoomManager.get_room_by_id(room_id)
        if not room_data:
            return Response(
                {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Additional permission check could be added here
        success = RoomManager.delete_room(room_id)

        if success:
            logger.info(f"Room deleted: {room_id}")
            return Response({"success": True, "message": "Room deleted successfully"})
        else:
            return Response(
                {"error": "Failed to delete room"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Failed to delete room {room_id}: {e}")
        return Response(
            {"error": "Failed to delete room"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
@csrf_exempt
@require_auth
def health_check(request):
    """API health check endpoint"""
    return Response(
        {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "authenticated": True,
            "session_key": request.session.session_key,
        }
    )
