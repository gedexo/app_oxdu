document.addEventListener('click', function(e) {
    let target = e.target;
    
    // Check if the clicked element has the attribute data-bs-toggle="remove"
    if (target.getAttribute('data-bs-toggle') === 'remove') {
        let closestAttachSupportFiles = closestWithClass(target, 'attach-supportfiles');
        
        // Check if an element with the class 'attach-supportfiles' is found
        if (closestAttachSupportFiles) {
            closestAttachSupportFiles.remove();
            e.preventDefault();
        }
    }
});

// Helper function to find the closest ancestor with a specific class
function closestWithClass(element, className) {
    while (element && !element.classList.contains(className)) {
        element = element.parentElement;
    }
    return element;
}