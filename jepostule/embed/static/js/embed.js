(function() {
    "use strict";
    var form = document.querySelector("form");
    var attachmentsInput = document.querySelector("input[name='attachments']");
    var attachments = [];
    var max_attachments_size = 10*1024*1024;// 10 Mb

    function sendMessage(action, label, value) {
        window.parent.postMessage({
            topic: "jepostule",
            action: action,
            label: label,
            value: value,
        }, "*");
    }

    /* Navigation */
    function displayStep() {
        // Navigate to data step pointed by location hash, or the first data step if it cannot be found
        document.querySelectorAll("[data-step]").forEach(function(step) {
            step.setAttribute('hidden', '');
        });
        var visibleStep = document.querySelector("[data-step='" + window.location.hash.substring(1) + "']") || document.querySelector("[data-step]");
        visibleStep.removeAttribute('hidden');
        visibleStep.scrollIntoView();

        // Warn parent window of navigation event
        sendMessage('navigate', "#" + visibleStep.attributes["data-step"].value);

        // Warn parent window that height may have changed
        sendMessage("resize", "height", window.document.documentElement.scrollHeight);
    }
    function onClickQuit(e) {
        e.preventDefault();
        sendMessage("quit", e.target.attributes.href.value);
    }
    displayStep();
    window.onhashchange = displayStep;

    // Synchronize form fields that share the same name
    function onFieldChange(e) {
        syncFormField(e.target);
    }
    function syncFormField(element) {
        // Fill form value
        var formInput = document.querySelector("form [readonly][name='" + element.name + "']");
        formInput.value = element.value;
    }
    document.querySelectorAll("[data-watchchanges]").forEach(function(input) {
        input.addEventListener("change", onFieldChange);
    });

    // Load some field values from local storage
    function loadFromLocalStorage(input) {
        var value = localStorage.getItem(input.name);
        if (value !== null && value.length > 0) {
            input.value = value;
            input.dispatchEvent(new Event('change'), {'bubbles': true});
        }
    }
    function saveToLocalStorage(input) {
        console.log("save", input.name, input.value);
        if(input.value.length > 0) {
            localStorage.setItem(input.name, input.value);
        }
    }
    function forEachLocalStorageElement(func) {
        document.querySelectorAll("[data-localstorage]").forEach(func);
    }
    forEachLocalStorageElement(loadFromLocalStorage);

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

        // Synchronize form fields: this is required because the "change" event
        // may not be fired when the user moves the cursor from the textarea
        // directly to the "next" button.
        document.querySelectorAll("[data-watchchanges]").forEach(function(input) {
            syncFormField(input);
        });

        // Save values to local storage
        forEachLocalStorageElement(saveToLocalStorage);

        // Validate asynchronously
        var formData = new FormData(form);
        var request = new XMLHttpRequest();
        request.open("POST", '/embed/validate/');
        request.addEventListener('load', function(e) {
            // In case of errors, just fail silently. Happy debugging!
            var result = true;
            var data = JSON.parse(e.target.responseText);
            for(var name in data.errors) {
                result = false;
                displayErrors(name, data.errors[name]);
            }
            if(result && callback) {
                callback();
            }
        });
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

    /* Attachments */
    // Heavily inspired by https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file#Examples

    // Click "Ajouter un document" button
    document.getElementById("attachments-add").addEventListener('click', function() {
        document.querySelector("input[name='attachments']").click();
    });
    attachmentsInput.addEventListener('change', function(e) {
        for(var i = 0; i < attachmentsInput.files.length; i++) {
            sendMessage('attachments', 'add');
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
        // This is ugly, and would be better handled by css, but it's badly
        // supported by IE 11
        if (attachments.length === 0) {
            document.getElementById("attachments-add").classList.remove("button-light");
            document.getElementById("attachments-continue").style.display = 'none';
            document.getElementById("no-attachments-continue").style.display = 'block';
            document.querySelector('.attachments-empty').style.display = 'block';
        } else {
            document.getElementById("attachments-add").classList.add("button-light");
            document.getElementById("attachments-continue").style.display = 'block';
            document.getElementById("no-attachments-continue").style.display = 'none';
            document.querySelector('.attachments-empty').style.display = 'none';
        }
    }
    function clickRemoveAttachment(e) {
        sendMessage('attachments', 'remove');
        var name = e.target.parentElement.firstElementChild.textContent;
        for(var i = 0; i < attachments.length; i++) {
            if (attachments[i].name == name) {
                attachments.splice(i, 1);
            }
        }
        updateAttachments();
    }

    // Refresh authentication token frequently
    (function refreshTokenLater() {
        window.setTimeout(function() {
            var formData = new FormData(form);
            var request = new XMLHttpRequest();
            request.open("POST", '/auth/application/token/refresh/');
            request.addEventListener('load', function(e) {
                if(e.target.status === 200) {
                    var data = JSON.parse(e.target.responseText);
                    document.querySelector("[name='token']").value = data.token;
                    document.querySelector("[name='timestamp']").value = data.timestamp;
                } else if (e.target.status >= 500) {
                    // Don't do anything, otherwise everyone writing an
                    // application during a deployment will see an error.
                } else {
                    window.location.hash = "#erreur-authentification";
                }
            });
            request.addEventListener('loadend', function(e) {
                refreshTokenLater();
            });
        request.send(formData);
        }, 60000);
    })();

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

        var formSubmit = document.querySelector("[type='submit']");
        formSubmit.setAttribute("disabled", '');
        var request = new XMLHttpRequest();
        request.addEventListener('load', function(e) {
            if (e.target.status >= 500) {
                window.location.hash = '#erreur';
            } else {
                document.querySelector("[data-step='fin']").innerHTML = request.responseText;
                window.location.hash = '#fin';
                document.querySelectorAll(".quit a").forEach(function(element) {
                    element.addEventListener("click", onClickQuit);
                });
            }
        });
        request.upload.addEventListener('progress', function(e) {
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
        request.open("POST", form.action);
        request.send(formData);
    }
})();
