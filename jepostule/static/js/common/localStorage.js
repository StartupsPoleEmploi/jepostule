'use strict'

document.addEventListener('DOMContentLoaded', function () {

  let useLocalStorage = inputs => {

    if (!inputs.length) {
      return
    }

    let saveToLocalStorage = (e) => {
      let input = e.target
      if (input.value) {
        localStorage.setItem(input.name, input.value)
      }
    }

    // Load from local storage.
    Array.from(inputs).forEach(input => {
      let value = localStorage.getItem(input.name)
      if (value) {
        input.value = value
        input.dispatchEvent(new Event('change'), {'bubbles': true})
      }
      input.addEventListener('blur', saveToLocalStorage)
    })

  }

  useLocalStorage(document.querySelectorAll('[data-localstorage]'))

})
