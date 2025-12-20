<!-- src/components/MediaControls.vue - Media control buttons component -->
<script setup>
import { ref, watch } from 'vue'
import { useWebRTCStore } from '../stores/webrtc'
import { useMediaDevices } from '../composables/useMediaDevices'

const webrtcStore = useWebRTCStore()
const {
  videoDevices,
  audioDevices,
  selectedVideoDevice,
  selectedAudioDevice,
  switchVideoDevice: switchVideo,
  switchAudioDevice: switchAudio,
} = useMediaDevices()

// Reactive state
const showSettings = ref(false)
const selectedQuality = ref('720p')

// Quality presets
const qualityPresets = {
  '720p': { width: 1280, height: 720 },
  '480p': { width: 640, height: 480 },
  '360p': { width: 480, height: 360 },
}

// Methods
const toggleVideo = () => {
  webrtcStore.toggleVideo()
}

const toggleAudio = () => {
  webrtcStore.toggleAudio()
}

const switchVideoDevice = async () => {
  try {
    if (selectedVideoDevice.value) {
      // Stop current stream
      if (webrtcStore.localStream) {
        webrtcStore.localStream.getVideoTracks().forEach((track) => track.stop())
      }

      // Create new stream with selected device
      const constraints = {
        video: {
          deviceId: selectedVideoDevice.value,
          ...qualityPresets[selectedQuality.value],
        },
        audio: selectedAudioDevice.value
          ? {
              deviceId: selectedAudioDevice.value,
            }
          : true,
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      webrtcStore.localStream = stream

      // Replace video track in peer connection if it exists
      if (webrtcStore.peerConnection) {
        const newVideoTrack = stream.getVideoTracks()[0]
        if (newVideoTrack) {
          const senders = webrtcStore.peerConnection.getSenders()
          const videoSender = senders.find(sender => sender.track && sender.track.kind === 'video')
          if (videoSender) {
            await videoSender.replaceTrack(newVideoTrack)
          }
        }
      }
    }
  } catch (error) {
    console.error('Failed to switch video device:', error)
  }
}

const switchAudioDevice = async () => {
  try {
    if (selectedAudioDevice.value) {
      // Similar logic for audio device switching
      if (webrtcStore.localStream) {
        webrtcStore.localStream.getAudioTracks().forEach((track) => track.stop())
      }

      const constraints = {
        video: selectedVideoDevice.value
          ? {
              deviceId: selectedVideoDevice.value,
              ...qualityPresets[selectedQuality.value],
            }
          : true,
        audio: {
          deviceId: selectedAudioDevice.value,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      webrtcStore.localStream = stream

      // Replace audio track in peer connection if it exists
      if (webrtcStore.peerConnection) {
        const newAudioTrack = stream.getAudioTracks()[0]
        if (newAudioTrack) {
          const senders = webrtcStore.peerConnection.getSenders()
          const audioSender = senders.find(sender => sender.track && sender.track.kind === 'audio')
          if (audioSender) {
            await audioSender.replaceTrack(newAudioTrack)
          }
        }
      }
    }
  } catch (error) {
    console.error('Failed to switch audio device:', error)
  }
}

const changeVideoQuality = async () => {
  try {
    if (webrtcStore.localStream && selectedQuality.value) {
      const videoTrack = webrtcStore.localStream.getVideoTracks()[0]
      if (videoTrack) {
        const constraints = qualityPresets[selectedQuality.value]
        await videoTrack.applyConstraints(constraints)
      }
    }
  } catch (error) {
    console.error('Failed to change video quality:', error)
  }
}

</script>

<template>
  <div class="flex justify-center space-x-4 mb-6">
    <!-- Video Toggle -->
    <button
      @click="toggleVideo"
      :class="[
        'control-button transform hover:scale-110 transition-transform',
        webrtcStore.isVideoEnabled ? 'control-button-active' : 'control-button-inactive',
      ]"
      :title="webrtcStore.isVideoEnabled ? 'Turn off camera' : 'Turn on camera'"
      :disabled="!webrtcStore.localStream"
    >
      <svg
        v-if="webrtcStore.isVideoEnabled"
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
        ></path>
      </svg>
      <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18 21l-1.5-1.5m-6.364-6.364L8.5 14.5 7 13l1.636-1.636"
        ></path>
      </svg>
    </button>

    <!-- Audio Toggle -->
    <button
      @click="toggleAudio"
      :class="[
        'control-button transform hover:scale-110 transition-transform',
        webrtcStore.isAudioEnabled ? 'control-button-active' : 'control-button-inactive',
      ]"
      :title="webrtcStore.isAudioEnabled ? 'Mute microphone' : 'Unmute microphone'"
      :disabled="!webrtcStore.localStream"
    >
      <svg
        v-if="webrtcStore.isAudioEnabled"
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
        ></path>
      </svg>
      <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1m0 0V7a3 3 0 013-3h8a3 3 0 013 3v2M4 9h1m11 0h5m-9 0a1 1 0 011-1v-1a1 1 0 011-1m-1 1v1a1 1 0 001 1M9 7h8a3 3 0 013 3v2"
        ></path>
      </svg>
    </button>

    <!-- Settings Button -->
    <button
      @click="showSettings = !showSettings"
      class="control-button control-button-inactive transform hover:scale-110 transition-transform"
      title="Video settings"
    >
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
        ></path>
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        ></path>
      </svg>
    </button>
  </div>

  <!-- Settings Panel -->
  <div v-if="showSettings" class="mt-4 card p-4 animate-slide-up">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Video Settings</h3>

    <!-- Video Devices -->
    <div v-if="videoDevices.length > 0" class="mb-4">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >Camera</label
      >
      <select v-model="selectedVideoDevice" @change="switchVideoDevice" class="input-field">
        <option v-for="device in videoDevices" :key="device.deviceId" :value="device.deviceId">
          {{ device.label || `Camera ${videoDevices.indexOf(device) + 1}` }}
        </option>
      </select>
    </div>

    <!-- Audio Devices -->
    <div v-if="audioDevices.length > 0" class="mb-4">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >Microphone</label
      >
      <select v-model="selectedAudioDevice" @change="switchAudioDevice" class="input-field">
        <option v-for="device in audioDevices" :key="device.deviceId" :value="device.deviceId">
          {{ device.label || `Microphone ${audioDevices.indexOf(device) + 1}` }}
        </option>
      </select>
    </div>

    <!-- Video Quality Settings -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >Video Quality</label
      >
      <select v-model="selectedQuality" @change="changeVideoQuality" class="input-field">
        <option value="720p">HD (720p)</option>
        <option value="480p">SD (480p)</option>
        <option value="360p">Low (360p)</option>
      </select>
    </div>


    <!-- Close Settings -->
    <div class="mt-4 flex justify-end">
      <button @click="showSettings = false" class="btn-secondary px-4 py-2">Done</button>
    </div>
  </div>
</template>

<style scoped>
.control-button {
  transition: all 0.2s ease-in-out;
}

.control-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}
</style>