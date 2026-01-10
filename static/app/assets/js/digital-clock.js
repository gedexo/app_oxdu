// Digital clock 
function updateClock(clockElement) {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timeString = `${hours}:${minutes}:${seconds}`;

    clockElement.textContent = timeString;
}

const clockElements = document.querySelectorAll('.digital-clock');

clockElements.forEach((clockElement) => {
    updateClock(clockElement);
});


setInterval(() => {
    clockElements.forEach((clockElement) => {
        updateClock(clockElement);
    });
}, 1000);
// Digital clock