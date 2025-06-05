<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Generated Email for {{ business.business_name }}</h3>
        <button class="close-button" @click="close">&times;</button>
      </div>
      
      <div class="modal-body">
        <div v-if="loading" class="loading">
          Generating email...
        </div>
        <div v-else-if="error" class="error">
          {{ error }}
        </div>
        <div v-else class="email-content">
          <div class="email-actions">
            <button @click="copyToClipboard" class="copy-button">
              Copy to Clipboard
            </button>
          </div>
          <pre class="email-text">{{ email }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { API_BASE_URL } from '../config'
import { useToast } from 'vue-toastification'

export default {
  name: 'EmailModal',
  props: {
    show: {
      type: Boolean,
      required: true
    },
    business: {
      type: Object,
      required: true
    }
  },
  setup() {
    const toast = useToast()
    return { toast }
  },
  data() {
    return {
      email: '',
      loading: false,
      error: null
    }
  },
  created() {
    console.log('EmailModal created with props:', {
      show: this.show,
      business: this.business
    })
  },
  watch: {
    show: {
      immediate: true,
      handler(newVal) {
        console.log('Show prop changed:', newVal)
        if (newVal) {
          console.log('Triggering email generation')
          this.generateEmail()
        }
      }
    },
    business: {
      immediate: true,
      handler(newVal) {
        console.log('Business prop changed:', newVal)
      }
    }
  },
  methods: {
    async generateEmail() {
      console.log('Starting email generation')
      this.loading = true
      this.error = null
      
      console.log('Generating email for business:', this.business)
      console.log('Business ID type:', typeof this.business.id)
      console.log('Business ID value:', this.business.id)
      console.log('API URL:', `${API_BASE_URL}/generate_email`)
      
      try {
        const requestData = {
          business_id: this.business.id,
          user_prompt_template: "Focus on offering modern, responsive web design services that will help their business grow online."
        }
        console.log('Request data:', requestData)
        
        // Log the full request details
        console.log('Making API call to:', `${API_BASE_URL}/generate_email`)
        console.log('With headers:', {
          'Content-Type': 'application/json'
        })
        
        const response = await axios.post(`${API_BASE_URL}/generate_email`, requestData, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        console.log('Email generation response:', response.data)
        
        if (!response.data.email) {
          throw new Error('No email content in response')
        }
        
        this.email = response.data.email
      } catch (error) {
        console.error('Error generating email:', error)
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          console.error('Error response data:', error.response.data)
          console.error('Error response status:', error.response.status)
          console.error('Error response headers:', error.response.headers)
        } else if (error.request) {
          // The request was made but no response was received
          console.error('Error request:', error.request)
        } else {
          // Something happened in setting up the request that triggered an Error
          console.error('Error message:', error.message)
        }
        this.error = error.response?.data?.error || error.message || 'Error generating email'
        this.toast.error(this.error)
      } finally {
        this.loading = false
      }
    },
    async copyToClipboard() {
      try {
        await navigator.clipboard.writeText(this.email)
        this.toast.success('Email copied to clipboard')
      } catch (error) {
        this.toast.error('Failed to copy email')
      }
    },
    close() {
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #721c24;
  background-color: #f8d7da;
  padding: 1rem;
  border-radius: 4px;
  margin: 1rem 0;
}

.email-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.email-actions {
  display: flex;
  justify-content: flex-end;
}

.copy-button {
  padding: 0.5rem 1rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.copy-button:hover {
  background-color: #3aa876;
}

.email-text {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  white-space: pre-wrap;
  font-family: Arial, sans-serif;
  line-height: 1.5;
  margin: 0;
}
</style> 