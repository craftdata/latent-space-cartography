import Store from '../controllers/store'

const config_logo = {
  dataset: 'logo',
  train_split: 15000,
  ext: 'jpg'
}

const config_emoji = {
  dataset: 'emoji',
  train_split: 13500,
  ext: 'png'
}

/**
 * Toggle dataset here!
 */
let c = config_logo

const DEBUG = process.env.NODE_ENV === 'development'
const DATASET = c.dataset
const TRAIN_SPLIT = c.train_split
const IMG_EXT = c.ext

/**
 * Only outputs if we are in dev build.
 */
function log_debug (...args) {
  if (DEBUG) {
    console.log(...args)
  }
}

/**
 * Shared store.
 */
let store = new Store()

export {
  DEBUG,
  TRAIN_SPLIT,
  IMG_EXT,
  DATASET,
  store,
  log_debug
}

