(function(){
    // Heavily inspired by https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file#Examples
    'use strict';
    var attachmentsInput = document.getElementById('id_attachments');
    var attachments = [];

    attachmentsInput.addEventListener('change', function(e) {
        for(var i = 0; i < attachmentsInput.files.length; i++) {
            attachments.push(attachmentsInput.files.item(i));
        }
        drawAttachments();
    });

    function drawAttachments() {
        var fileList = document.getElementById('id_attachments-list');
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
            remove.src = '/static/img/times.svg';
            remove.addEventListener('click', clickRemove);
        }
    }
    function clickRemove(e) {
        var name = e.target.parentElement.firstElementChild.textContent;
        for(var i = 0; i < attachments.length; i++) {
            if (attachments[i].name == name) {
                attachments.splice(i, 1);
            }
        }
        drawAttachments();
    }
})();
