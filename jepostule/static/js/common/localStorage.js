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

    Array.from(inputs).forEach(input => {
      // Load value from local storage.
      let value = localStorage.getItem(input.name)
      if (value) {
        input.value = value
        input.dispatchEvent(new Event('change'), {'bubbles': true})
      }
      // Save value to local storage.
      input.addEventListener('blur', saveToLocalStorage)
    })

  }

  useLocalStorage(document.querySelectorAll('[data-localstorage]'))

})
