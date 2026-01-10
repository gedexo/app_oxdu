

(function () {
    "use strict";

    /* Successful notifications */
    var options = {
        animationDuration: 0.3,
        position: "top-right",
    };{
        options.durations = {
            successButtons: 10,
          };

    }

    var notifier = new AWN(options);

    // Select all elements with the class "successful-notify"
    var successButtons = document.querySelectorAll('.successful-notify');
    // Add event listener to each button
    successButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            notifier.success('<p class="mb-0"><i class="fa-solid fa-check fs-18 me-2 d-inline-block"></i>Well done Details Submitted Successfully</p>');
        });
    });

})();
