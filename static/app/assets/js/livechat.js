"use strict";
document.addEventListener("click", function(event) {
  if (event.target.id === "chat-popup") {
      event.preventDefault();
      var chatMessagePopup = document.querySelector('.chat-message-popup');
      chatMessagePopup.classList.toggle('active');

      var chatPopup = document.getElementById("chat-popup");
      chatPopup.classList.remove('chat-popup-active');
  }
});
  
  // ChatEnd Chat
  document.querySelector(".popup-minimize-normal")?.addEventListener("click", function(event) {
      event.preventDefault();
      const chatMessagePopup = document.querySelector('.chat-message-popup');
      chatMessagePopup.classList.add('popup-endchat');
  });
  
  // Go Back
  document.addEventListener("click", function(event) {
    if (event.target.classList.contains("goback-chat")) {
      event.preventDefault();
      const chatMessagePopup = document.querySelector('.chat-message-popup');
      chatMessagePopup.classList.remove('popup-endchat');
    }
  });
  
  // Chat Rating
  document.addEventListener("click", function(event) {
    if (event.target.classList.contains("end-chat-button")) {
      event.preventDefault();
      const chatMessagePopup = document.querySelector('.chat-message-popup');
      chatMessagePopup.classList.add('rating-section-body');
      chatMessagePopup.classList.remove('popup-endchat');
    }
  });
  
  document.addEventListener("click", function(event) {
    if (event.target.classList.contains("btn-chat-close")) {
      event.preventDefault();
      const chatMessagePopup = document.querySelector('.chat-message-popup');
      chatMessagePopup.classList.remove('card-fullscreen');
      setTimeout(function() {
        chatMessagePopup.classList.remove('active');
      }, 500);
    }
  });
  
  /* chat-popup Button */

  document.addEventListener("click", function(event) {
    if (event.target.classList.contains("popup-minimize")) {
        event.preventDefault();
        var chatMessagePopup = document.querySelector('.chat-message-popup');
        var chatPopup = document.getElementById('chat-popup');

        chatMessagePopup.classList.remove('active');
        chatMessagePopup.classList.remove('card-fullscreen');
        chatPopup.classList.add('chat-popup-active');
    }
});