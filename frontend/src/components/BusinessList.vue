<template>
  <div class="business-list">
    <div class="header">
      <h2>Businesses</h2>
      <button 
        v-if="businesses.length > 0"
        @click="confirmClear" 
        class="clear-btn"
      >
        Clear All Data
      </button>
    </div>
    
    <div class="filters">
      <input 
        v-model="filters.business_name" 
        :placeholder="`Search by ${columnMapping.business_name?.displayName || 'Business Name'}`"
        @input="fetchBusinesses"
      >
      <input 
        v-model="filters.industry" 
        :placeholder="`Filter by ${columnMapping.industry?.displayName || 'Industry'}`"
        @input="fetchBusinesses"
      >
      <input 
        v-model="filters.location" 
        :placeholder="`Filter by ${columnMapping.location?.displayName || 'Location'}`"
        @input="fetchBusinesses"
      >
    </div>

    <div v-if="loading" class="loading">
      Loading businesses...
    </div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else-if="businesses.length === 0" class="no-data">
      No businesses found
    </div>

    <div v-else class="business-grid">
      <div v-for="business in businesses" :key="business.id" class="business-card">
        <h3>{{ business.business_name }}</h3>
        <p class="industry">
          <span class="field-label">Industry:</span>
          {{ business.industry_display_name || business.industry }}
        </p>
        <div class="location-tags">
          <span v-if="business.city" class="location-tag city">{{ business.city }}</span>
          <span v-if="business.state" class="location-tag state">{{ business.state }}</span>
        </div>
        <p class="location">{{ business.location }}</p>
        <div class="website-status">
          <span :class="['status', business.website ? 'has-website' : 'no-website']">
            {{ business.website ? 'Has Website' : 'No Website' }}
          </span>
          <a 
            v-if="business.website" 
            :href="business.website" 
            target="_blank" 
            class="website-link"
          >
            {{ business.website }}
          </a>
        </div>
        <div class="action-buttons">
          <button 
            v-if="!business.website"
            @click="findWebsite(business.id)"
            :disabled="isSearchingWebsite === business.id"
            class="find-website-btn"
          >
            {{ isSearchingWebsite === business.id ? 'Searching...' : 'Find Website' }}
          </button>
          <button 
            @click="() => {
              console.log('Email button clicked for business:', business);
              openEmailModal(business);
            }"
            class="email-btn"
          >
            Generate Email
          </button>
        </div>
      </div>
    </div>

    <div class="pagination" v-if="totalPages > 1">
      <button 
        @click="changePage(currentPage - 1)"
        :disabled="currentPage === 1"
      >
        Previous
      </button>
      <span>Page {{ currentPage }} of {{ totalPages }}</span>
      <button 
        @click="changePage(currentPage + 1)"
        :disabled="currentPage === totalPages"
      >
        Next
      </button>
    </div>

    <EmailModal
      v-if="selectedBusiness"
      :show="isEmailModalOpen"
      :business="selectedBusiness"
      @close="closeEmailModal"
    />
  </div>
</template>

<script>
import axios from 'axios'
import { API_BASE_URL } from '../config'
import { useToast } from 'vue-toastification'
import EmailModal from './EmailModal.vue'

export default {
  name: 'BusinessList',
  components: {
    EmailModal
  },
  setup() {
    const toast = useToast()
    return { toast }
  },
  data() {
    return {
      businesses: [],
      loading: false,
      error: null,
      filters: {
        business_name: '',
        industry: '',
        location: ''
      },
      columnMappingData: {
        business_name: { displayName: 'Business Name' },
        industry: { displayName: 'Industry' },
        location: { displayName: 'Location' }
      },
      currentPage: 1,
      perPage: 10,
      totalPages: 1,
      isSearchingWebsite: null,
      isEmailModalOpen: false,
      selectedBusiness: null
    }
  },
  computed: {
    columnMapping() {
      return this.columnMappingData
    }
  },
  mounted() {
    this.fetchBusinesses()
    this.fetchColumnMapping()
  },
  methods: {
    async fetchColumnMapping() {
      try {
        const response = await axios.get(`${API_BASE_URL}/column_mapping`)
        this.columnMappingData = response.data.mapping
      } catch (error) {
        console.error('Error fetching column mapping:', error)
      }
    },
    async fetchBusinesses() {
      this.loading = true
      this.error = null

      try {
        const params = {
          page: this.currentPage,
          per_page: this.perPage,
          business_name: this.filters.business_name.toLowerCase(),
          industry: this.filters.industry.toLowerCase(),
          location: this.filters.location.toLowerCase()
        }

        const response = await axios.get(`${API_BASE_URL}/businesses`, { params })
        this.businesses = response.data.businesses
        this.totalPages = response.data.total_pages
      } catch (error) {
        const errorMessage = error.response?.data?.error || 'Error fetching businesses'
        this.error = errorMessage
        this.toast.error(errorMessage)
      } finally {
        this.loading = false
      }
    },
    async findWebsite(businessId) {
      console.log('Finding website for business ID:', businessId)
      this.isSearchingWebsite = businessId

      try {
        const response = await axios.get(`${API_BASE_URL}/businesses/${businessId}/website`)
        console.log('Website search response:', response.data)
        
        // Update the business in the list
        const index = this.businesses.findIndex(b => b.id === businessId)
        if (index !== -1) {
          this.businesses[index] = response.data.business
          if (response.data.business.website) {
            this.toast.success(`Found website for ${response.data.business.business_name}`)
          } else {
            this.toast.warning(`No website found for ${response.data.business.business_name}`)
          }
        }
      } catch (error) {
        const errorMessage = error.response?.data?.error || 'Error finding website'
        console.error('Error finding website:', error.response?.data || error)
        this.toast.error(errorMessage)
      } finally {
        this.isSearchingWebsite = null
      }
    },
    async clearData() {
      try {
        await axios.post(`${API_BASE_URL}/clear`)
        this.businesses = []
        this.currentPage = 1
        this.totalPages = 1
        this.filters = {
          business_name: '',
          industry: '',
          location: ''
        }
        this.toast.success('All business data cleared successfully')
      } catch (error) {
        const errorMessage = error.response?.data?.error || 'Error clearing data'
        console.error('Error clearing data:', error.response?.data || error)
        this.toast.error(errorMessage)
      }
    },
    confirmClear() {
      if (confirm('Are you sure you want to clear all business data? This action cannot be undone.')) {
        this.clearData()
      }
    },
    changePage(page) {
      this.currentPage = page
      this.fetchBusinesses()
    },
    openEmailModal(business) {
      console.log('Opening email modal for business:', business)
      this.selectedBusiness = { ...business }  // Create a new object to ensure reactivity
      this.isEmailModalOpen = true
      console.log('Modal state:', {
        selectedBusiness: this.selectedBusiness,
        isEmailModalOpen: this.isEmailModalOpen
      })
    },
    closeEmailModal() {
      console.log('Closing email modal')
      this.isEmailModalOpen = false
      this.selectedBusiness = null
    }
  }
}
</script>

<style scoped>
.business-list {
  margin-top: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.clear-btn {
  padding: 0.5rem 1rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s ease;
}

.clear-btn:hover {
  background-color: #c82333;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filters input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.business-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.business-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.business-card h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.industry, .location {
  color: #666;
  margin: 0.25rem 0;
  font-size: 0.9rem;
}

.location-tags {
  display: flex;
  gap: 0.5rem;
  margin: 0.5rem 0;
}

.location-tag {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.location-tag.city {
  background-color: #e3f2fd;
  color: #1976d2;
}

.location-tag.state {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.website-status {
  margin: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.status.has-website {
  background-color: #d4edda;
  color: #155724;
}

.status.no-website {
  background-color: #f8d7da;
  color: #721c24;
}

.website-link {
  color: #42b983;
  text-decoration: none;
  font-size: 0.9rem;
  word-break: break-all;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.website-link:hover {
  text-decoration: underline;
  background-color: #e9ecef;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.find-website-btn,
.email-btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.find-website-btn {
  background-color: #42b983;
  color: white;
}

.find-website-btn:hover {
  background-color: #3aa876;
}

.find-website-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.email-btn {
  background-color: #2196f3;
  color: white;
}

.email-btn:hover {
  background-color: #1976d2;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.pagination button {
  padding: 0.5rem 1rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading, .error, .no-data {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #721c24;
  background-color: #f8d7da;
  border-radius: 4px;
}

/* Add styles to ensure modal is visible */
:deep(.modal-overlay) {
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

:deep(.modal-content) {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

/* Add new style for field label */
.field-label {
  font-weight: 500;
  color: #2c3e50;
  margin-right: 0.5rem;
}
</style> 