(function() {
    "use strict";
    /* Navigation */
    function displayStep() {
        document.querySelectorAll("[data-step]").forEach(function(step) {
            step.setAttribute('hidden', '');
        });
        var visibleStep = document.querySelector("[data-step='" + window.location.hash.substring(1) + "']") || document.querySelector("[data-step='bienvenue']");
        visibleStep.removeAttribute('hidden');
    }
    displayStep();
    window.onpopstate = displayStep;

    /* Form validation */
    function updateFormField(e) {
        // Film form value
        var formInput = document.querySelector("form input[readonly][name='" + e.target.name + "']");
        if(formInput !== null) {
            formInput.value = e.target.value;
        }

        // Validation
        var body = new FormData();
        body.append(e.target.name, e.target.value);
        // TODO fetch polyfill
        fetch('/embed/validate/', {
            method: 'POST',
            body: body
        }).then(function(response) {
            return response.json();
        }).then(function(data) {
            for(var name in data.errors) {
                // TODO
                console.log(name, data.errors[name]);
            }
        });
    }
    document.querySelectorAll("input,textarea").forEach(function(input) {
        input.addEventListener("change", updateFormField);
    });
    
    /* Attachments */
    // Heavily inspired by https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file#Examples
    function initAttachments() {
        document.getElementById("attachments-add").addEventListener('click', function() {
            document.querySelector("input[name='attachments']").click();
        });

        var attachmentsInput = document.querySelector("input[name='attachments']");
        var attachments = [];

        attachmentsInput.addEventListener('change', function(e) {
            for(var i = 0; i < attachmentsInput.files.length; i++) {
                attachments.push(attachmentsInput.files.item(i));
            }
            drawAttachments();
        });

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
            drawAttachments();
        }

        var form = document.querySelector("form");
        form.addEventListener("submit", function(evt) {
            evt.preventDefault();
            var formData = new FormData(form);
            for (var i = 0; i < attachments.length; i++) {
                formData.append('attachments', attachments[i], attachments[i].name);
            }

            var formSubmit = document.querySelector("[type='submit']");
            formSubmit.setAttribute("disabled", '');
            var request = new XMLHttpRequest();
            request.open("POST", form.action);
            request.onload = function(e) {
                document.querySelector("[data-step='fin']").innerHTML = request.responseText;
                window.location.hash = '#fin';
            };
            request.send(formData);
                //success: function(html) {
                    //updateModal(html);
                    //initUploadedButtons();
                    //ga('send', 'event', 'Tilkee', 'upload', siret);
                //},
                //error: function(jqXHR, textStatus, errorThrown) {
                    //if (jqXHR.status === 413) {
                        //updateModal("Vos documents sont de trop grande taille : veuillez sélectionner des documents dont la taille totale est inférieure à 10 Mo.");
                    //} else if (jqXHR.status >= 500) {
                        //updateModal("Une erreur inattendue s'est produite : nos équipes ont été prévenues et vont essayer de résoudre le problème très rapidement. Merci de réessayer plus tard.");
                    //} else {
                        //updateModal("Erreur " + String(jqXHR.status) + " : est-ce que par hasard vous n'auriez pas essayé de faire quelque chose de fourbe ?");
                    //}
                    //ga('send', 'event', 'Tilkee', 'upload-error', siret);
                //},
                //complete: function() {
                    //$form.find("[type='submit']").prop("disabled", false);
                //},
                //xhr: function() {
                    //// Monitor upload progress
                    //var $messageElt = $tilkeeModal.find(".upload-progress-message");

                    //$tilkeeModal.find(".progressbar").removeClass("hidden");
                    //$messageElt.removeClass("hidden");
                    //var xhr = $.ajaxSettings.xhr();
                    //if (xhr.upload) {
                        //xhr.upload.addEventListener('progress', function(e) {
                            //if (e.lengthComputable) {
                                //var percentage = e.loaded * 100/e.total;
                                //$tilkeeModal.find(".progressbar span").css("width", String(percentage) + "%");
                                //if (percentage < 100) {
                                    //$messageElt.html("1/2 Envoi de vos fichiers...");
                                //} else {
                                    //$messageElt.html("2/2 Création de votre dossier...");
                                //}
                            //}
                        //} , false);
                    //}
                    //return xhr;
                //},
            //});
        });
    }
    initAttachments();
})();
