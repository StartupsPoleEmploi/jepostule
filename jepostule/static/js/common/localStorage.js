'use strict'

document.addEventListener('DOMContentLoaded', function () {

  useLocalStorage(document.querySelectorAll('[data-localstorage]'))

})

let useLocalStorage = inputs => {

  if (!inputs.length) {
    return
  }

  // Load from local storage.
  Array.from(inputs).forEach(input => {
    let value = localStorage.getItem(input.name)
    if (value) {
      input.value = value
      input.dispatchEvent(new Event('change'), {'bubbles': true})
    }
  })

  let saveToLocalStorage = (e) => {
    let input = e.target
    if (input.value) {
      localStorage.setItem(input.name, input.value)
    }
  }

  Array.from(inputs).forEach(el => {
    el.addEventListener('blur', saveToLocalStorage)
  })

}
