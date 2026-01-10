"use strict";
	// vertical swiper
    var swiper1 = new Swiper(".popular-articles-swiper", {
        direction: "vertical",
        slidesPerView: 3,
        spaceBetween: 2,
        loop: true,
        autoplay: {
            delay: 1500,
            disableOnInteraction: false
        },
        breakpoints: {
            // Set breakpoints for different screen sizes
            375: {
              slidesPerView: 4,
              spaceBetween: 1,
            },
          },
    });