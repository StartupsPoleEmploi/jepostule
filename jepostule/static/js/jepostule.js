(function() {
    "use strict";
    var form = document.querySelector("form");
    var attachmentsInput = document.querySelector("input[name='attachments']");
    var attachments = [];
    var max_attachments_size = 10*1024*1024;// 10 Mb


    /* Navigation */
    function displayStep() {
        document.querySelectorAll("[data-step]").forEach(function(step) {
            step.setAttribute('hidden', '');
        });
        var visibleStep = document.querySelector("[data-step='" + window.location.hash.substring(1) + "']") || document.querySelector("[data-step]");
        visibleStep.removeAttribute('hidden');
    }
    displayStep();
    window.onpopstate = displayStep;

    /* Form and attachments validation */
    function clickValidateApplication(e) {
        // Maybe we could display a spinner here? In theory, form validation
        // should be pretty quick.
        e.preventDefault();
        validateApplication(function() {
            window.location.hash = e.target.attributes.href.value;
        });
    }
    function validateApplication(callback) {
        /* Perform form validation. If successful, run callback. Else, display errors. */

        // Clear errors
        document.querySelectorAll("[data-errors]:not([data-errors='attachments'])").forEach(function(fieldErrors) {
            fieldErrors.innerHTML = '';
        });

        // Validate asynchronously
        var formData = new FormData(form);
        var request = new XMLHttpRequest();
        request.open("POST", '/embed/validate/');
        request.onload = function(e) {
            var result = true;
            var data = JSON.parse(e.target.responseText);
            for(var name in data.errors) {
                result = false;
                displayErrors(name, data.errors[name]);
            }
            if(result && callback) {
                callback();
            }
        };
        request.send(formData);
    }
    function clickValidateAttachments(e) {
        e.preventDefault();
        validateAttachments(function() {
            window.location.hash = e.target.attributes.href.value;
        });
    }
    function validateAttachments(callback) {
        // Clear errors
        document.querySelectorAll("[data-errors='attachments']").forEach(function(fieldErrors) {
            fieldErrors.innerHTML = '';
        });

        // Validate total size
        var totalSize = 0;
        for(var i = 0; i < attachments.length; i++) {
            totalSize += attachments[i].size;
        }
        if(totalSize > max_attachments_size) {
            var message = "La taille de vos pièces jointes est trop élevée : " + (totalSize / (1024*1024)).toFixed(1);
            message += " Mo. Max: " + (max_attachments_size / (1024*1024)).toFixed(0) + " Mo.";
            displayErrors('attachments', [message]);
        } else {
            if(callback) {
                callback();
            }
        }
    }
    function displayErrors(name, errors) {
        document.querySelectorAll("[data-errors='" + name + "']").forEach(function(fieldErrors) {
            for(var i = 0; i < errors.length; i++) {
                var item = document.createElement('li');
                fieldErrors.appendChild(item);
                item.textContent = errors[i];
            }
        });
    }
    document.querySelectorAll(".validate-application").forEach(function(element) {
        element.addEventListener("click", clickValidateApplication);
    });
    document.querySelectorAll(".validate-attachments").forEach(function(element) {
        element.addEventListener("click", clickValidateAttachments);
    });

    // Synchronize form fields that share the same name
    function updateFormField(e) {
        // Film form value
        var formInput = document.querySelector("form input[readonly][name='" + e.target.name + "']");
        if(formInput !== null) {
            formInput.value = e.target.value;
        }
    }
    document.querySelectorAll("input,textarea").forEach(function(input) {
        input.addEventListener("change", updateFormField);
    });

    // Load some field values from local storage
    var storageprefix = "";
    function loadValue(input) {
        if(input.value.length == 0) {
            var value = localStorage.getItem(input.name);
            if (value !== null) {
                input.value = value;
                input.dispatchEvent(new Event('change'), {'bubbles': true});
            }
        }
    }
    function saveValue(e) {
        if(e.target.value.length > 0) {
            localStorage.setItem(e.target.name, e.target.value);
        }
    }
    document.querySelectorAll("input[data-localstorage]").forEach(function(input) {
        loadValue(input);
        input.addEventListener("change", saveValue);
    });
    
    /* Attachments */
    // Heavily inspired by https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file#Examples

    // Click "Ajouter un document" button
    document.getElementById("attachments-add").addEventListener('click', function() {
        document.querySelector("input[name='attachments']").click();
    });
    attachmentsInput.addEventListener('change', function(e) {
        for(var i = 0; i < attachmentsInput.files.length; i++) {
            attachments.push(attachmentsInput.files.item(i));
        }
        updateAttachments();
    });

    function updateAttachments() {
        validateAttachments();
        drawAttachments();
    }
    function drawAttachments() {
        // Display list of attachments with X to remove
        document.querySelectorAll('.attachments-list').forEach(function(fileList) {
            fileList.innerHTML = '';
            var list = document.createElement('ul');
            fileList.appendChild(list);
            for(var i = 0; i < attachments.length; i++) {
                var item = document.createElement('li');
                list.appendChild(item);

                var name = document.createElement('span');
                item.appendChild(name);
                name.textContent = attachments[i].name;

                var remove = document.createElement('img');
                item.appendChild(remove);
                remove.src = '/static/img/icons/times.svg';
                remove.addEventListener('click', clickRemoveAttachment);
            }
        });

        // Show/Hide corresponding buttons
        document.querySelectorAll('[data-count]').forEach(function(element) {
            element.dataset.count = attachments.length;
        });
    }
    function clickRemoveAttachment(e) {
        var name = e.target.parentElement.firstElementChild.textContent;
        for(var i = 0; i < attachments.length; i++) {
            if (attachments[i].name == name) {
                attachments.splice(i, 1);
            }
        }
        updateAttachments();
    }

    // Catch form submission to add attachments on the fly
    form.addEventListener("submit", function(evt) {
        evt.preventDefault();
        submitForm();
    });

    function submitForm() {
        var formData = new FormData(form);
        for (var i = 0; i < attachments.length; i++) {
            formData.append('attachments', attachments[i], attachments[i].name);
        }

        // TODO: add ga events
        var formSubmit = document.querySelector("[type='submit']");
        formSubmit.setAttribute("disabled", '');
        var request = new XMLHttpRequest();
        request.open("POST", form.action);
        request.addEventListener('load', function(e) {
            if (e.target.status >= 500) {
                window.location.hash = '#erreur';
            } else {
                document.querySelector("[data-step='fin']").innerHTML = request.responseText;
                window.location.hash = '#fin';
            }
        });
        request.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                document.querySelector(".progressbar").removeAttribute('hidden');
                var percentComplete = e.loaded * 100 / e.total;
                var progressbar = document.querySelector(".progressbar span");
                progressbar.style.width = String(percentComplete) + "%";
            }
        });
        request.addEventListener('loadend', function(e) {
            formSubmit.removeAttribute("disabled");
        });
        request.send(formData);
    }
})();
