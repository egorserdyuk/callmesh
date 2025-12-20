<!-- src/components/VideoPreview.vue - Complete local video preview component -->
<template>
  <div class="relative">
    <div class="video-container aspect-video max-w-2xl mx-auto">
      <!-- Video Element -->
      <video
        ref="videoRef"
        autoplay
        muted
        playsinline
        class="w-full h-full object-cover"
        :class="{ mirror: webrtcStore.shouldMirror }"
      ></video>


      <!-- No video placeholder -->
      <div
        v-if="!webrtcStore.hasLocalVideo || !webrtcStore.isVideoEnabled"
        class="absolute inset-0 flex items-center justify-center bg-gray-800"
      >
        <div class="text-center">
          <div
            class="w-20 h-20 bg-gray-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse-slow"
          >
            <svg
              class="w-10 h-10 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              ></path>
            </svg>
          </div>
          <p class="text-gray-400 text-lg font-medium">
            {{ !webrtcStore.hasLocalVideo ? 'No camera detected' : 'Camera is off' }}
          </p>
          <p class="text-gray-500 text-sm mt-2">
            {{
              !webrtcStore.hasLocalVideo
                ? 'Check your camera connection'
                : 'Click the camera button to turn on'
            }}
          </p>
        </div>
      </div>

      <!-- Loading overlay -->
      <div
        v-if="isInitializing"
        class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50"
      >
        <div class="text-center text-white">
          <div
            class="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"
          ></div>
          <p class="text-lg font-medium">{{ loadingMessage }}</p>
        </div>
      </div>

      <!-- Video quality indicator -->
      <div
        v-if="webrtcStore.hasLocalVideo && showQualityIndicator"
        class="absolute top-4 right-4 flex items-center space-x-2 bg-black bg-opacity-50 px-3 py-2 rounded-lg text-white text-sm"
      >
        <div
          :class="[
            'w-3 h-3 rounded-full',
            videoQuality === 'high'
              ? 'bg-green-400'
              : videoQuality === 'medium'
                ? 'bg-yellow-400'
                : 'bg-red-400',
          ]"
        ></div>
        <span>{{ videoQualityText }}</span>
      </div>
    </div>

    <!-- Media access error -->
    <div
      v-if="mediaError"
      class="mt-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4 animate-fade-in"
    >
      <div class="flex">
        <svg
          class="w-5 h-5 text-yellow-400 mt-0.5 mr-3 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
          ></path>
        </svg>
        <div class="flex-1">
          <p class="text-sm text-yellow-800 dark:text-yellow-300 font-medium">
            Camera access needed
          </p>
          <p class="text-sm text-yellow-700 dark:text-yellow-400 mt-1">{{ mediaError }}</p>
          <div class="mt-3 flex space-x-3">
            <button
              @click="initializeMedia"
              class="text-sm bg-yellow-100 hover:bg-yellow-200 dark:bg-yellow-800 dark:hover:bg-yellow-700 text-yellow-800 dark:text-yellow-200 px-3 py-1 rounded-md font-medium transition-colors"
            >
              Try again
            </button>
            <button
              @click="showPermissionHelp = !showPermissionHelp"
              class="text-sm text-yellow-600 dark:text-yellow-400 underline hover:no-underline"
            >
              Need help?
            </button>
          </div>

          <!-- Permission help -->
          <div
            v-if="showPermissionHelp"
            class="mt-3 p-3 bg-yellow-100 dark:bg-yellow-800/30 rounded-md"
          >
            <p class="text-sm text-yellow-700 dark:text-yellow-300 font-medium mb-2">
              To enable camera access:
            </p>
            <ul class="text-xs text-yellow-600 dark:text-yellow-400 space-y-1">
              <li>• Click the camera icon in your browser's address bar</li>
              <li>• Select "Allow" when prompted for camera permission</li>
              <li>• Refresh the page if needed</li>
              <li>• Make sure no other app is using your camera</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useWebRTCStore } from '../stores/webrtc'
import { mediaService } from '../services/media'

const webrtcStore = useWebRTCStore()

// Template refs
const videoRef = ref(null)

// Reactive state
const mediaError = ref('')
const isInitializing = ref(false)
const loadingMessage = ref('')
const showPermissionHelp = ref(false)
const showQualityIndicator = ref(false)
const videoQuality = ref('high')

// Computed
const videoQualityText = computed(() => {
  switch (videoQuality.value) {
    case 'high':
      return 'HD'
    case 'medium':
      return 'SD'
    case 'low':
      return 'Low'
    default:
      return 'Unknown'
  }
})

// Methods
const initializeMedia = async () => {
  try {
    isInitializing.value = true
    mediaError.value = ''
    loadingMessage.value = 'Accessing camera and microphone...'

    const result = await webrtcStore.initializeLocalMedia()

    if (!result.success) {
      mediaError.value = result.error
      showQualityIndicator.value = false
    } else {
      showQualityIndicator.value = true
      detectVideoQuality()
    }
  } catch (error) {
    console.error('Failed to initialize media:', error)
    mediaError.value = 'Failed to access camera or microphone'
  } finally {
    isInitializing.value = false
  }
}

const toggleVideo = () => {
  webrtcStore.toggleVideo()
  if (webrtcStore.isVideoEnabled) {
    detectVideoQuality()
  }
}

const toggleAudio = () => {
  webrtcStore.toggleAudio()
}

const detectVideoQuality = () => {
  if (!webrtcStore.localStream) return

  const videoTrack = webrtcStore.localStream.getVideoTracks()[0]
  if (videoTrack) {
    const settings = videoTrack.getSettings()
    const width = settings.width || 0

    if (width >= 1280) {
      videoQuality.value = 'high'
    } else if (width >= 640) {
      videoQuality.value = 'medium'
    } else {
      videoQuality.value = 'low'
    }
  }
}

const handlePermissionDenied = () => {
  mediaError.value =
    'Camera and microphone access denied. Please allow permissions in your browser settings and refresh the page.'
  showPermissionHelp.value = true
}

const checkMediaPermissions = async () => {
  try {
    const permissions = await mediaService.checkMediaPermissions()
    if (permissions.camera === 'denied' || permissions.microphone === 'denied') {
      handlePermissionDenied()
    }
  } catch (error) {
    console.warn('Could not check media permissions:', error)
  }
}

// Watch for local stream changes
watch(
  () => webrtcStore.localStream,
  (newStream) => {
    if (videoRef.value && newStream) {
      videoRef.value.srcObject = newStream
    }
  },
  { immediate: true },
)

// Watch for video enabled changes
watch(
  () => webrtcStore.isVideoEnabled,
  (enabled) => {
    if (enabled) {
      detectVideoQuality()
    }
  },
)

// Lifecycle
onMounted(async () => {
  await initializeMedia()
  await checkMediaPermissions()

  // Show quality indicator after 2 seconds
  setTimeout(() => {
    if (webrtcStore.hasLocalVideo) {
      showQualityIndicator.value = true
    }
  }, 2000)
})

onUnmounted(() => {
  // Cleanup is handled by the WebRTC store
})
</script>

<style scoped>
.mirror {
  transform: scaleX(-1);
}

.video-container {
  position: relative;
  overflow: hidden;
}

.control-button {
  transition: all 0.2s ease-in-out;
}

.control-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

/* Custom animations */
@keyframes pulse-slow {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse-slow {
  animation: pulse-slow 3s ease-in-out infinite;
}

/* Custom scrollbar for settings */
.settings-scroll::-webkit-scrollbar {
  width: 4px;
}

.settings-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.settings-scroll::-webkit-scrollbar-thumb {
  background: rgba(156, 163, 175, 0.5);
  border-radius: 2px;
}

.settings-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 0.7);
}
</style>
