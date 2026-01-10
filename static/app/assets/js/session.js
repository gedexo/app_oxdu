
    'use strict';
    
    var myModal11 = new bootstrap.Modal(document.getElementById('myModal11'), {})
    myModal11.toggle()

    setInterval(function () {
        var progress = document.getElementById('custom-bar');

        if (progress.value < progress.max) {
            progress.value += 10;
        }
    }, 1000);