'use strict'

document.addEventListener('DOMContentLoaded', function () {

  var useLocalStorage = function (inputs) {

    if (!inputs.length) {
      return
    }

    var saveToLocalStorage = function (e) {
      var input = e.target
      if (input.value) {
        localStorage.setItem(input.name, input.value)
      }
    }

    inputs.forEach(function (input) {
      // Load value from local storage.
      var value = localStorage.getItem(input.name)
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
