<template>
  <!--Modal for Uploading Group-->
  <b-modal id="modal-upload" ref="modalUpload"
           title="Upload" hide-footer>
    <div class="text-muted text-sm">
      First, select which field you use to represent each sample.
      Then paste the samples, separated by comma, into the text box below.
      Alternatively, upload a CSV file with no header and only one column.
    </div>
    <div class="mt-3 mb-3">
      <!--Choose field-->
      <div class="mb-3 text-center bd-subtitle text-uppercase">Which field?</div>
      <b-form-group class="text-sm">
        <b-form-radio-group v-model="field" :options="all_fields"></b-form-radio-group>
      </b-form-group>
    </div>
    <div class="mt-3 mb-3">
      <!--Paste-->
      <div class="mb-3 text-center bd-subtitle text-uppercase">Paste</div>
      <b-form-textarea v-model="csv_string" type="text" :rows="3" class="text-sm"
                       :placeholder="placeholders[field]"></b-form-textarea>
      <div class="text-right mt-3">
        <button class="mr-2 btn btn-sm btn-light" v-if="csv_string"
                @click="csv_string=''">Clear</button>
        <button class="btn btn-primary btn-sm" style="min-width: 100px;"
                @click="parseString"
                v-if="csv_string">Done</button>
      </div>
    </div>
    <div>
      <!--Divider-->
      <div class="d-flex justify-content-center">
        <div class="bd-text-divider"></div>
        <div class="text-muted text-sm ml-2 mr-2">OR</div>
        <div class="bd-text-divider"></div>
      </div>
    </div>
    <div class="mt-3 mb-3">
      <!--Upload File-->
      <div class="mb-3 text-center bd-subtitle text-uppercase">Upload File</div>
      <div class="d-flex justify-content-between">
        <b-form-file v-model="file" plain class="text-sm"></b-form-file>
        <button class="btn btn-primary btn-sm" style="min-width: 100px;"
                @click="parseFile" v-if="file">Upload</button>
      </div>
    </div>

    <!--Error-->
    <div class="mt-3 mb-3 text-danger text-sm" v-if="err">{{err}}</div>
  </b-modal>
</template>

<script>
  import {store} from '../controllers/config'
  import _ from 'lodash'
  import Papa from 'papaparse'

  const csv_config = {
    delimiter: ','
  }

  function namesToIndices (arr) {
    let map = {}
    _.each(store.meta, (p) => {
      map[p.name] = p.i
    })

    return _.filter(_.map(arr, (n) => map[n]), (n) => _.isNumber(n))
  }

  function validIndex (arr) {
    let map = {}
    _.each(store.meta, (p) => {
      map[p.i] = true
    })

    return _.filter(arr, (n) => map[n])
  }

  export default {
    name: 'GroupUploadModal',
    data () {
      return {
        csv_string: '',
        file: null,
        field: 'i',
        all_fields: [
          {text: 'Index', value: 'i'},
          {text: 'Patient ID (name)', value: 'name'}
        ],
        placeholders: {
          'i': 'For example: 1,5,16,289',
          'name': 'For example: TCGA-02-0055-01,TCGA-02-2483-01,TCGA-02-2485-01'
        },
        err: ''
      }
    },
    watch: {
      csv_string: function () {
        this.err = ''
      },
      field: function () {
        this.err = ''
      },
      file: function () {
        this.err = ''
      }
    },
    methods: {
      parseFile () {
        Papa.parse(this.file, {
          complete: (res) => {
            if (res.data && res.data.length) {
              this.parse(res)
            } else {
              // handle error
              console.log(res.errors)
              this.err = 'Could not parse the file.'
            }
          },
          error: (err) => {
            // handle error
            console.log(err)
            this.err = 'Could not parse the file.'
          }
        })
      },
      parseString () {
        let res = Papa.parse(this.csv_string, csv_config)
        if (res && !res.errors.length) {
          this.parse(res)
        } else {
          // handle error
          console.log(res.errors)
          this.err = 'Could not parse the content.'
        }
      },

      // common parse helper
      parse (res) {
        let arr = _.flatten(res.data)

        if (this.field === 'i') {
          arr = validIndex(arr)
          arr = _.map(arr, (n) => Number(n))
        } else if (this.field === 'name') {
          arr = namesToIndices(arr)
        }

        if (!arr.length) {
          this.err = 'No valid samples found. Did you choose the right field?'
        } else {
          store.addToSelected(arr)
          this.$refs.modalUpload.hide()
        }
      }
    }
  }
</script>

<style>
  .bd-text-divider {
    border-bottom: #818078 1px solid;
    height: 0.7em;
    width: 15%;
  }
</style>
