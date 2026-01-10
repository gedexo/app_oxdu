(function ($) {
    ("use strict");
  
    /*--------------------------------------------------------------
   ## Down Load Button Function
     ----------------------------------------------------------------*/
    //  $("#download_btn").on("click", function () {
    //   var downloadSection = $("#download_section")[0];
    
    //   var cWidth = downloadSection.offsetWidth;
    //   var cHeight = downloadSection.offsetHeight;
    
    //   var topLeftMargin = 40;
    //   var scaleFactor = 2; 
    
    //   html2canvas(downloadSection, {
    //     scale: scaleFactor, 
    //     allowTaint: true,
    //     useCORS: true
    //   }).then(function (canvas) {
    //     var imgData = canvas.toDataURL("image/jpeg", 1.0);
    
    //     var imgWidth = cWidth;
    //     var imgHeight = cHeight;
    
    //     var pdfWidth = imgWidth + topLeftMargin * 2;
    //     var pdfHeight = (pdfWidth * 1.5) + topLeftMargin * 2;
    
    //     var totalPDFPages = Math.ceil(imgHeight / pdfHeight) - 1;
    
    //     var pdf = new jsPDF("p", "pt", [pdfWidth, pdfHeight]);
    //     pdf.addImage(
    //       imgData,
    //       "JPEG",
    //       topLeftMargin,
    //       topLeftMargin,
    //       imgWidth,
    //       imgHeight
    //     );
    
    //     for (var i = 1; i <= totalPDFPages; i++) {
    //       pdf.addPage(pdfWidth, pdfHeight);
    //       pdf.addImage(
    //         imgData,
    //         "JPEG",
    //         topLeftMargin,
    //         -(pdfHeight * i) + topLeftMargin,
    //         imgWidth,
    //         imgHeight
    //       );
    //     }
    
    //     pdf.save("salary_slip.pdf");
    //   });
    // });

    $("#download_btn").on("click", function () {
      var downloadSection = $("#download_section")[0];

      var originalOverflow = downloadSection.style.overflow;
      var originalWidth = downloadSection.style.width;

      downloadSection.style.overflow = 'scroll';
      downloadSection.style.width = '850px'

      var cWidth = downloadSection.scrollWidth;
      var cHeight = downloadSection.scrollHeight;

      var topLeftMargin = 40;
      var scaleFactor = 2;

      html2canvas(downloadSection, {
          scale: scaleFactor,
          width: cWidth,
          height: cHeight,
          allowTaint: true,
          useCORS: true,
          scrollX: 0,
          scrollY: 0,
          windowWidth: cWidth,
          windowHeight: cHeight
      }).then(function (canvas) {
          var imgData = canvas.toDataURL("image/jpeg", 1.0);

          var imgWidth = cWidth;
          var imgHeight = cHeight;

          var pdfWidth = imgWidth + topLeftMargin * 2;
          var pdfHeight = (pdfWidth * 1.5) + topLeftMargin * 2;

          var totalPDFPages = Math.ceil(imgHeight / pdfHeight) - 1;

          var pdf = new jsPDF("p", "pt", [pdfWidth, pdfHeight]);
          pdf.addImage(
              imgData,
              "JPEG",
              topLeftMargin,
              topLeftMargin,
              imgWidth,
              imgHeight
          );

          for (var i = 1; i <= totalPDFPages; i++) {
              pdf.addPage(pdfWidth, pdfHeight);
              pdf.addImage(
                  imgData,
                  "JPEG",
                  topLeftMargin,
                  -(pdfHeight * i) + topLeftMargin,
                  imgWidth,
                  imgHeight
              );
          }

          pdf.save("salary_slip.pdf");

          // Restore original styles
          downloadSection.style.overflow = originalOverflow;
          downloadSection.style.width = originalWidth;
      });
  });

    $("#copybtn1").on("click", function () {
      let text = document.getElementById("myText1");
      navigator.clipboard.writeText(text.innerHTML);
    });
  
    /* Copy text */
  
    $("#copybtn2").on("click", function () {
      let text2 = document.getElementById("myText2");
      navigator.clipboard.writeText(text2.innerText);
    });
  })(jQuery);