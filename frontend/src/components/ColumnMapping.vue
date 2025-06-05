<template>
  <div class="column-mapping" v-if="show">
    <h3>Map CSV Columns</h3>
    <p class="help-text">Please map your CSV columns to the required fields and set their display names</p>

    <div class="mapping-grid">
      <div class="mapping-item" v-for="(field, index) in requiredFields" :key="field">
        <label :for="field">{{ capitalize(field.replace('_', ' ')) }}</label>
        <div class="mapping-inputs">
          <select 
            :id="field" 
            v-model="mapping[field].column"
            :class="{ 'error': !mapping[field].column }"
          >
            <option value="">Select a column</option>
            <option 
              v-for="column in availableColumns" 
              :key="column"
              :value="column"
              :disabled="isColumnMapped(column) && mapping[field].column !== column"
            >
              {{ column }}
            </option>
          </select>
          <input 
            type="text"
            v-model="mapping[field].displayName"
            :placeholder="`Display name for ${capitalize(field.replace('_', ' '))}`"
            class="display-name-input"
          >
        </div>
      </div>
    </div>

    <div class="preview">
      <h4>Data Preview</h4>
      <div class="preview-table">
        <table>
          <thead>
            <tr>
              <th v-for="column in availableColumns" :key="column">
                {{ column }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in previewData" :key="index">
              <td v-for="column in availableColumns" :key="column">
                {{ row[column] }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="actions">
      <button 
        @click="cancel" 
        class="cancel-btn"
      >
        Cancel
      </button>
      <button 
        @click="confirm" 
        :disabled="!isMappingValid"
        class="confirm-btn"
      >
        Confirm Mapping
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ColumnMapping',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    csvData: {
      type: Array,
      default: () => []
    },
    csvColumns: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      requiredFields: ['business_name', 'industry', 'location'],
      mapping: {
        business_name: { column: '', displayName: 'Business Name' },
        industry: { column: '', displayName: 'Industry' },
        location: { column: '', displayName: 'Location' }
      }
    }
  },
  computed: {
    availableColumns() {
      return this.csvColumns
    },
    previewData() {
      return this.csvData.slice(0, 5) // Show first 5 rows
    },
    isMappingValid() {
      return this.requiredFields.every(field => this.mapping[field].column)
    }
  },
  methods: {
    capitalize(str) {
      return str.charAt(0).toUpperCase() + str.slice(1)
    },
    isColumnMapped(column) {
      return Object.values(this.mapping).some(m => m.column === column)
    },
    cancel() {
      this.$emit('cancel')
    },
    confirm() {
      if (this.isMappingValid) {
        this.$emit('confirm', this.mapping)
      }
    }
  }
}
</script>

<style scoped>
.column-mapping {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 1rem;
}

.help-text {
  color: #666;
  margin-bottom: 1.5rem;
}

.mapping-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.mapping-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mapping-item label {
  font-weight: bold;
  color: #2c3e50;
}

.mapping-inputs {
  display: flex;
  gap: 1rem;
}

.mapping-inputs select,
.mapping-inputs input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.display-name-input {
  min-width: 150px;
}

.mapping-item select.error {
  border-color: #dc3545;
}

.preview {
  margin: 2rem 0;
}

.preview h4 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.preview-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border: 1px solid #ddd;
}

th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.cancel-btn, .confirm-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s ease;
}

.cancel-btn {
  background-color: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background-color: #5a6268;
}

.confirm-btn {
  background-color: #42b983;
  color: white;
}

.confirm-btn:hover {
  background-color: #3aa876;
}

.confirm-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style> 