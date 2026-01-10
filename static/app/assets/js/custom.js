(function () {
    "use strict";

    /* page loader */

    function hideLoader() {
        $("#loader").addClass("d-none");
    }

    $(window).on("load", hideLoader);

    /* page loader */

    /* tooltip */
    const tooltipTriggerList = document.querySelectorAll(
        '[data-bs-toggle="tooltip"]'
    );
    const tooltipList = [...tooltipTriggerList].map(
        (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
    );

    /* popover  */
    const popoverTriggerList = document.querySelectorAll(
        '[data-bs-toggle="popover"]'
    );
    const popoverList = [...popoverTriggerList].map(
        (popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl)
    );

    //switcher color pickers
    const pickrContainerPrimary = document.querySelector(
        ".pickr-container-primary"
    );
    const themeContainerPrimary = document.querySelector(
        ".theme-container-primary"
    );
    const pickrContainerBackground = document.querySelector(
        ".pickr-container-background"
    );
    const themeContainerBackground = document.querySelector(
        ".theme-container-background"
    );

    /* for theme primary */
    const nanoThemes = [
        [
            "nano",
            {
                defaultRepresentation: "RGB",
                components: {
                    preview: true,
                    opacity: false,
                    hue: true,

                    interaction: {
                        hex: false,
                        rgba: true,
                        hsva: false,
                        input: true,
                        clear: false,
                        save: false,
                    },
                },
            },
        ],
    ];

    /* for theme background */
    const nanoThemes1 = [
        [
            "nano",
            {
                defaultRepresentation: "RGB",
                components: {
                    preview: true,
                    opacity: false,
                    hue: true,

                    interaction: {
                        hex: false,
                        rgba: true,
                        hsva: false,
                        input: true,
                        clear: false,
                        save: false,
                    },
                },
            },
        ],
    ];



    /* Choices JS */
    document.addEventListener("DOMContentLoaded", function () {
        var genericExamples = document.querySelectorAll("[data-trigger]");
        for (let i = 0; i < genericExamples.length; ++i) {
            var element = genericExamples[i];
            new Choices(element, {
                allowHTML: true,
                placeholderValue: "This is a placeholder set in the config",
                searchPlaceholderValue: "Search",
            });
        }
    });
    /* Choices JS */

    /* node waves */
    Waves.attach(".btn-wave", ["waves-light"]);
    Waves.init();
    /* node waves */

    /* card with close button */
    let DIV_CARD = ".card";
    let cardRemoveBtn = document.querySelectorAll(
        '[data-bs-toggle="card-remove"]'
    );
    cardRemoveBtn.forEach((ele) => {
        ele.addEventListener("click", function (e) {
            e.preventDefault();
            let $this = this;
            let card = $this.closest(DIV_CARD);
            card.remove();
            return false;
        });
    });
    /* card with close button */

    /* card with fullscreen */
    let cardFullscreenBtn = document.querySelectorAll(
        '[data-bs-toggle="card-fullscreen"]'
    );
    cardFullscreenBtn.forEach((ele) => {
        ele.addEventListener("click", function (e) {
            let $this = this;
            let card = $this.closest(DIV_CARD);
            card.classList.toggle("card-fullscreen");
            card.classList.remove("card-collapsed");
            e.preventDefault();
            return false;
        });
    });
    /* card with fullscreen */

    /* count-up */
    var i = 1;
    setInterval(() => {
        document.querySelectorAll(".count-up").forEach((ele) => {
            if (ele.getAttribute("data-count") >= i) {
                i = i + 1;
                ele.innerText = i;
            }
        });
    }, 10);
    /* count-up */

    /* back to top */
    const scrollToTop = document.querySelector(".scrollToTop");
    const $rootElement = document.documentElement;
    const $body = document.body;
    window.onscroll = () => {
        const scrollTop = window.scrollY || window.pageYOffset;
        const clientHt = $rootElement.scrollHeight - $rootElement.clientHeight;
        if (window.scrollY > 100) {
            scrollToTop.style.display = "flex";
        } else {
            scrollToTop.style.display = "none";
        }
    };
    scrollToTop.onclick = () => {
        window.scrollTo(0, 0);
    };
    /* back to top */
})();

/* full screen */
var elem = document.documentElement;
function openFullscreen() {
    let open = document.querySelector(".full-screen-open");
    let close = document.querySelector(".full-screen-close");
    let elem = document.documentElement; // Fullscreen for the whole document

    // Check if we are already in fullscreen mode
    if (
        !document.fullscreenElement &&
        !document.webkitFullscreenElement &&
        !document.msFullscreenElement
    ) {
        // Enter fullscreen mode if not already in fullscreen
        if (elem.requestFullscreen) {
            elem.requestFullscreen();
        } else if (elem.webkitRequestFullscreen) {
            /* Safari */
            elem.webkitRequestFullscreen();
        } else if (elem.msRequestFullscreen) {
            /* IE11 */
            elem.msRequestFullscreen();
        }

        // Update button visibility and set the cookie to remember fullscreen state
        close.classList.add("d-block");
        close.classList.remove("d-none");
        open.classList.add("d-none");

        setCookie("fullscreen", "true", 365); // Store fullscreen state in cookie for 365 days
    } else {
        // Exit fullscreen mode if already in fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            /* Safari */
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            /* IE11 */
            document.msExitFullscreen();
        }

        // Update button visibility and set the cookie to remember fullscreen state
        close.classList.remove("d-block");
        open.classList.remove("d-none");
        close.classList.add("d-none");
        open.classList.add("d-block");

        setCookie("fullscreen", "false", 365); // Store fullscreen state in cookie for 365 days
    }
}
/* full screen */

/* toggle switches */
let customSwitch = document.querySelectorAll(".toggle");
customSwitch.forEach((e) =>
    e.addEventListener("click", () => {
        e.classList.toggle("on");
    })
);
/* toggle switches */

/* header dropdown close button */

/* for cart dropdown */
const headerbtn = document.querySelectorAll(".dropdown-item-close");
headerbtn.forEach((button) => {
    button.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        button.parentNode.parentNode.parentNode.parentNode.parentNode.remove();
        document.getElementById("cart-data").innerText = `${
            document.querySelectorAll(".dropdown-item-close").length
        } Items`;
        document.getElementById("cart-icon-badge").innerText = `${
            document.querySelectorAll(".dropdown-item-close").length
        }`;
        console.log(
            document.getElementById("header-cart-items-scroll").children.length
        );
        if (document.querySelectorAll(".dropdown-item-close").length == 0) {
            let elementHide = document.querySelector(".empty-header-item");
            let elementShow = document.querySelector(".empty-item");
            elementHide.classList.add("d-none");
            elementShow.classList.remove("d-none");
        }
    });
});
/* for cart dropdown */

// for table show count

$("#select-table_pagination").on("change", function () {
    var selectedValue = $(this).val();
    var currentUrl = new URL(window.location.href);

    // Update the URL parameter 'table_pagination'
    currentUrl.searchParams.set("table_pagination", selectedValue);

    // Redirect to the updated URL
    window.location.href = currentUrl.toString();
});

// for table serach

$("#table-search").on("submit", function (e) {
    e.preventDefault(); // Prevent the default form submission

    // Get the serialized form data
    var formData = $(this).serializeArray();
    var currentUrl = new URL(window.location.href);

    // Update search parameters in the URL
    formData.forEach(function (field) {
        currentUrl.searchParams.set(field.name, field.value);
    });

    // Redirect to the updated URL
    window.location.href = currentUrl.toString();
});

$(".form-horizontal select:not(.offcanvas select, .form-horizontal-invoice select, .form-horizontal-transaction select, .modal select, table select, #select-table_pagination, [multiple])").select2({
    minimumResultsForSearch: "",
    placeholder: "Search",
    width: "100%",
    allowClear: true,
});

function updateFieldValues(fields) {
    for (const [field, value] of Object.entries(fields)) {
        if (typeof value === 'number' && !isNaN(value)) {
            $(field).val(value.toFixed(2));
        } else {
            // Handle non-numeric values (optional)
            $(field).val(value); // or set to an empty string if you want
        }
    }
}

$('.dropdown-toggle').on('show.bs.dropdown', function () {
    $(this).closest('.table-responsive').css('overflow', 'visible');
  });
  
  $('.dropdown-toggle').on('hide.bs.dropdown', function () {
    $(this).closest('.table-responsive').css('overflow', 'auto');
  });

function handleFormSubmit(selectBoxId, modalId) {
    const select = $(selectBoxId); // Get the select box using the full ID (including '#')

    // Bind the submit event to the form inside the modal
    $(modalId + " form").submit(function (event) {
        event.preventDefault(); // Prevent the default form submission

        var form = $(this)[0]; // Ensure we have the form element
        if (!form || form.tagName !== "FORM") {
            console.error("The selected element is not a valid form.");
            alert("An error occurred. Please try again.");
            return;
        }
        var form_data = new FormData(form); // Create a FormData object with the form
        var account_add_url = $(form).attr("action"); // Get the action URL from the form
        // AJAX request to save account information
        makeAjaxCall(account_add_url,form_data,modalId,selectBoxId);
    });
}

function makeAjaxCall(url, data, modalId, select) {
    const select_element = $(select); // Store the select element
    const modal_element = $(modalId); // Store the modal element

    // Perform the AJAX call
    $.ajax({
        url: url, // The endpoint to call
        method: 'POST', // HTTP method
        data: data, // Data to send to the server
        processData: false,
        contentType: false, // Prevent jQuery from setting contentType
        success: function (response) {
            if (response.success && response.result) {
                const response_result = response.result;

                // Ensure both `id` and `name` exist in the response
                if (response_result.id && response_result.name) {
                    // Reset the form within the modal
                    modal_element.find('form')[0].reset();

                    // Hide the modal
                    modal_element.modal('hide');

                    // Add the new account to the select field and mark it as selected
                    select_element.append('<option value="' + response_result.id + '" selected>' + response_result.name + '</option>');
                } else {
                    console.error('Response is missing `id` or `name` fields:', response_result);
                    alert('Failed to add the new account. Please try again.');
                }
            } else {
                console.error('Invalid response:', response);
                alert('An error occurred. Please check your input and try again.');
            }
        },
        error: function (xhr, status, error) {
            console.error('AJAX Error:', status, error);
            alert('A server error occurred. Please try again later.');
        }
    });
}



document.querySelectorAll('select[multiple]').forEach((select) => {
    // Initialize Choices
    new Choices(select, {
      allowHTML: true,
      removeItemButton: true,
    });
  });
  


$(".select2").on("click", () => {
    let selectField = document.querySelectorAll(".select2-search__field");
    selectField.forEach((element, index) => {
        element?.focus();
    });
});

// for adding new button on select2
function initializeSelect2WithModal(selectId, modalTarget,placeholder) {
    setupSelect2($(selectId), modalTarget,placeholder);
}

function initializeSelect2ForFormRow(row, selectClass, modalTarget,placeholder) {
    setupSelect2(row.find(selectClass), modalTarget,placeholder);
}

function setupSelect2(selectElement, modalTarget,placeholder) {
    selectElement.select2({
        placeholder: placeholder,
        allowClear: true,
        dropdownCssClass: "custom-select2-dropdown",
        width: "100%",
    });

    selectElement.on("select2:open", function () {
        // Focus on the search input field
        setTimeout(
            () => document.querySelector(".select2-search__field")?.focus(),
            0
        );

        // Append "Add New" button if not already present
        if (!$(".select2-add-btn-container").length) {
            appendAddNewButton(modalTarget);
        }
    });
}

function appendAddNewButton(modalTarget) {
    const addButton = `
      <div class="select2-add-btn-container">
          <button type="button" class="btn btn-secondary btn-sm w-100 mt-2" 
                  data-bs-toggle="modal" data-bs-target="${modalTarget}">
              Add New
          </button>
      </div>`;
    $(".custom-select2-dropdown").append(addButton);

    $(".select2-add-btn-container button").on("click", function () {
        // Close visible Select2 dropdown
        $("select")
            .filter((_, el) => $(el).data("select2")?.$dropdown.is(":visible"))
            .select2("close");

        // Show the modal
        $($(this).data("bs-target")).modal("show");
    });
}

function bindSelect2Focus(selector) {
    $(selector).on("click", function () {
        const activeRow = $(this).closest(".formset_row");
        // Store or clear active row reference
        if (activeRow.length && activeRow.hasClass("formset_row")) {
            $("form").data("activeRow", activeRow);
        } else {
            $("form").removeData("activeRow");
        }

        $(".select2-search__field").focus();
    });
}

// Initialize date inputs
$("input.dateinput[type='date']").flatpickr({
    dateFormat: "Y-m-d", 
    allowInput: true,
    clickOpens: true
});

// Initialize datetime inputs
$("input.dateinput[type='datetime-local']").flatpickr({
    enableTime: true,
    dateFormat: "Y-m-d\TH:i", 
    allowInput: true,
    clickOpens: true
});

// Fallback for any remaining dateinput fields
$("input.dateinput:not([type='date']):not([type='datetime-local'])").flatpickr({
    dateFormat: "d/m/Y", 
    allowInput: true,
    clickOpens: true
});

flatpickr(".timeinput", {
    enableTime: true,
    noCalendar: true,
    dateFormat: "H:i",
    time_24hr: false
});

$(".form-horizontal").each(function () {
    $(this).addClass("row justify-content-between");
    $(this).find(".mb-3").addClass("col-lg-4 col-md-6 col-sm-6 col-12");
});
$("textarea").attr("rows", 3);

$(".orderable a").each(function () {
    if (!$(this).find(".fa").length) {
        $(this).append(' <i class="fa fa-sort"></i>');
    }
});

$('input[type="number"]').on("click", function () {
    $(this).select();
});

function submitFormAjax(form, data, url, activeRow, modal, elementClass) {
    console.log(activeRow);
    const method = "POST"; // Default method set to POST
    $.ajax({
        url: url,
        type: method,
        data: data,
        processData: false, // Prevent jQuery from processing the data
        contentType: false, // Prevent jQuery from setting the content type
        success: function (response) {
            if (activeRow) {
                // Extract the new item data from the response
                const newItem = response.result; // Replace with actual response structure

                if (newItem) {
                    // Update the Select2 dropdown in the active row
                    const selectElement = $(activeRow).find(elementClass);
                    const newOption = new Option(
                        newItem.name,
                        newItem.id,
                        true,
                        true
                    );
                    selectElement.append(newOption).trigger("change"); // Trigger change to update Select2
                }
            }

            form[0].reset();
            if (modal.length) {
                modal.modal("hide");
            }

            // Optional: Add additional success handling logic here
        },
        error: function (xhr, status, error) {
            // Handle errors
            console.error("Submission failed:", xhr.responseText || error);
        },
    });
}

/* for notifications dropdown */
const headerbtn1 = document.querySelectorAll(".dropdown-item-close1");
headerbtn1.forEach((button) => {
    button.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        button.parentNode.parentNode.parentNode.remove();
        document.getElementById("notifiation-data").innerText = `${
            document.querySelectorAll(".dropdown-item-close1").length
        } Unread`;
        // document.getElementById("notification-icon-badge").innerText = `${
        //   document.querySelectorAll(".dropdown-item-close1").length
        // }`;
        if (document.querySelectorAll(".dropdown-item-close1").length == 0) {
            let elementHide1 = document.querySelector(".empty-header-item1");
            let elementShow1 = document.querySelector(".empty-item1");
            elementHide1.classList.add("d-none");
            elementShow1.classList.remove("d-none");
        }
    });
});
/* for notifications dropdown */


// Toggle checkbox when clicking anywhere in the table cell
$('#selectable-table').on('click', '.checkbox-column', function(e) {
    // Don't trigger if clicking directly on the checkbox
    if ($(e.target).is('input[type="checkbox"]')) {
        return;
    }
    
    const checkbox = $(this).find('.select-checkbox');
    checkbox.prop('checked', !checkbox.prop('checked'));
    const allChecked = $('.select-checkbox:checked').length === $('.select-checkbox').length;
    $('.select-all-checkbox').prop('checked', allChecked);
    
    // Update delete button visibility
    toggleDeleteButton();
});

// Select all/deselect all functionality
$('.select-all-checkbox').on('change', function() {
    const isChecked = $(this).prop('checked');
    $('.select-checkbox').prop('checked', isChecked);
    
    // Update delete button visibility
    toggleDeleteButton();
});

// If any checkbox is unchecked, uncheck the "select all" checkbox
$('#selectable-table').on('change', '.select-checkbox', function() {
    const allChecked = $('.select-checkbox:checked').length === $('.select-checkbox').length;
    $('.select-all-checkbox').prop('checked', allChecked);
    
    // Update delete button visibility
    toggleDeleteButton();
});