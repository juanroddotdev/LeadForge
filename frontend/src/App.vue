<template>
  <div class="container">
    <h1>LeadForge</h1>
    <p class="subtitle">Web Design Lead Generation Tool</p>
    
    <div class="upload-section">
      <h2>Upload Business Data</h2>
      <p class="help-text">Upload a CSV file containing business information</p>
      
      <div class="upload-box" 
           @dragover.prevent 
           @drop.prevent="handleFileDrop"
           :class="{ 'is-dragover': isDragover }">
        <input 
          type="file" 
          ref="fileInput" 
          @change="handleFileSelect" 
          accept=".csv"
          class="file-input"
        >
        <div class="upload-content">
          <p v-if="!selectedFile">Drag and drop your CSV file here or click to browse</p>
          <p v-else>Selected file: {{ selectedFile.name }}</p>
        </div>
      </div>

      <div v-if="uploadStatus" :class="['status-message', uploadStatus.type]">
        {{ uploadStatus.message }}
      </div>

      <button 
        @click="previewFile" 
        :disabled="!selectedFile || isUploading"
        class="upload-button"
      >
        {{ isUploading ? 'Processing...' : 'Preview & Upload' }}
      </button>
    </div>

    <ColumnMapping
      v-if="showColumnMapping"
      :show="showColumnMapping"
      :csv-data="csvPreviewData"
      :csv-columns="csvColumns"
      @cancel="cancelMapping"
      @confirm="confirmMapping"
    />

    <BusinessList ref="businessList" />
  </div>
</template>

<script>
import axios from 'axios'
import BusinessList from './components/BusinessList.vue'
import ColumnMapping from './components/ColumnMapping.vue'
import Papa from 'papaparse'
import { API_BASE_URL } from './config'
import { useToast } from 'vue-toastification'

export default {
  name: 'App',
  components: {
    BusinessList,
    ColumnMapping
  },
  setup() {
    const toast = useToast()
    return { toast }
  },
  data() {
    return {
      selectedFile: null,
      isDragover: false,
      isUploading: false,
      uploadStatus: null,
      showColumnMapping: false,
      csvPreviewData: [],
      csvColumns: [],
      columnMapping: null
    }
  },
  methods: {
    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file && file.type === 'text/csv') {
        this.selectedFile = file
        this.uploadStatus = null
        this.uploadError = null
      } else {
        this.uploadStatus = {
          type: 'error',
          message: 'Please select a valid CSV file'
        }
      }
    },
    handleFileDrop(event) {
      this.isDragover = false
      const file = event.dataTransfer.files[0]
      if (file && file.type === 'text/csv') {
        this.selectedFile = file
        this.uploadStatus = null
        this.uploadError = null
      } else {
        this.uploadStatus = {
          type: 'error',
          message: 'Please drop a valid CSV file'
        }
      }
    },
    previewFile() {
      if (!this.selectedFile) return

      Papa.parse(this.selectedFile, {
        header: true,
        preview: 5, // Only parse first 5 rows for preview
        complete: (results) => {
          this.csvPreviewData = results.data
          this.csvColumns = results.meta.fields
          this.showColumnMapping = true
        },
        error: (error) => {
          this.uploadStatus = {
            type: 'error',
            message: 'Error parsing CSV file: ' + error.message
          }
        }
      })
    },
    cancelMapping() {
      this.showColumnMapping = false
      this.csvPreviewData = []
      this.csvColumns = []
      this.columnMapping = null
    },
    async confirmMapping(mapping) {
      this.columnMapping = mapping
      this.showColumnMapping = false
      await this.uploadFile()
    },
    async uploadFile() {
      if (!this.selectedFile || !this.columnMapping) return

      this.isUploading = true
      this.uploadStatus = null
      this.uploadError = null

      const formData = new FormData()
      formData.append('file', this.selectedFile)
      formData.append('column_mapping', JSON.stringify(this.columnMapping))

      // Debug logs
      console.log('Column Mapping:', this.columnMapping)
      console.log('FormData contents:')
      for (let pair of formData.entries()) {
        console.log(pair[0], pair[1])
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        this.uploadStatus = {
          type: 'success',
          message: `Successfully uploaded ${response.data.records_count} records`
        }
        this.toast.success('File uploaded successfully')
        this.selectedFile = null
        this.$refs.fileInput.value = ''
        this.columnMapping = null
        
        // Refresh the business list
        this.$refs.businessList?.fetchBusinesses()
      } catch (error) {
        const errorMessage = error.response?.data?.error || 'Error uploading file'
        this.uploadError = errorMessage
        this.toast.error(errorMessage)
      } finally {
        this.isUploading = false
      }
    }
  }
}
</script>

<style>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  font-family: Arial, sans-serif;
}

h1 {
  color: #2c3e50;
  text-align: center;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  text-align: center;
  margin-bottom: 2rem;
}

.upload-section {
  background: #f8f9fa;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.help-text {
  color: #666;
  margin-bottom: 1rem;
}

.upload-box {
  border: 2px dashed #ccc;
  border-radius: 4px;
  padding: 2rem;
  text-align: center;
  margin-bottom: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-box.is-dragover {
  border-color: #42b983;
  background-color: rgba(66, 185, 131, 0.1);
}

.file-input {
  display: none;
}

.upload-content {
  color: #666;
}

.upload-button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

.upload-button:hover {
  background-color: #3aa876;
}

.upload-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.status-message {
  margin: 1rem 0;
  padding: 0.75rem;
  border-radius: 4px;
}

.status-message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style> 