(function () {

    let confirmModal, successModal;
    let confirmBtn, confirmBtnText;

    document.addEventListener("DOMContentLoaded", function () {

        const confirmEl = document.getElementById("globalFeeRefreshModal");
        const successEl = document.getElementById("feeRefreshSuccessModal");

        if (!confirmEl || !successEl) return;

        confirmModal = new bootstrap.Modal(confirmEl);
        successModal = new bootstrap.Modal(successEl);

        confirmBtn = document.getElementById("confirmFeeRefreshBtn");
        confirmBtnText = confirmBtn.querySelector(".btn-text");

        // OPEN CONFIRM MODAL
        document.addEventListener("click", function (e) {
            const btn = e.target.closest("[data-fee-refresh]");
            if (!btn) return;

            e.preventDefault();
            confirmEl.dataset.url = btn.dataset.url;

            resetConfirmButton();
            confirmModal.show();
        });

        // CONFIRM REFRESH
        confirmBtn.addEventListener("click", function () {

            const url = confirmEl.dataset.url;
            if (!url) return;

            setModalLoading(true);

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "Accept": "application/json"
                }
            })
            .then(res => res.json())
            .then(data => {
                confirmModal.hide();
                setModalLoading(false);

                document.getElementById("feeRefreshSuccessMessage").innerText =
                    data.message || "Fee structure refreshed successfully.";

                successModal.show();
            })
            .catch(() => {
                setModalLoading(false);
                alert("Failed to refresh fee structure.");
            });
        });
    });

    // 🔄 MODAL BUTTON LOADING
    function setModalLoading(isLoading) {
        if (!confirmBtn) return;

        confirmBtn.disabled = isLoading;

        if (isLoading) {
            confirmBtnText.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2"></span>
                Processing...
            `;
        } else {
            // Updated text to match new HTML
            confirmBtnText.innerText = "Yes, Refresh it"; 
        }
    }


    function resetConfirmButton() {
        confirmBtn.disabled = false;
        confirmBtnText.innerText = "Yes, Refresh it";
    }

    // 🔐 CSRF TOKEN
    function getCSRFToken() {
        let token = null;
        document.cookie.split(";").forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith("csrftoken=")) {
                token = decodeURIComponent(cookie.substring(10));
            }
        });
        return token;
    }

})();
