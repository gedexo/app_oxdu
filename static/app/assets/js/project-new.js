 
 
 
 (function () {
    "use strict"
        // for product features
        var toolbarOptions = [
            [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
            [{ 'font': [] }],
            ['bold', 'italic', 'underline', 'strike'],        // toggled buttons
            ['blockquote', 'code-block'],

            [{ 'header': 1 }, { 'header': 2 }],               // custom button values
            [{ 'list': 'ordered' }, { 'list': 'bullet' }],

            [{ 'color': [] }, { 'background': [] }],          // dropdown with defaults from theme
            [{ 'align': [] }],
            ['clean']                                         // remove formatting button
        ];
        var quill = new Quill('#note', {
            modules: {
                toolbar: toolbarOptions
            },
            theme: 'snow'
        });


  /* default multi select */
  const secondElement = new Choices('#choices-multiple-default', { allowSearch: false }).setValue(['Choice 2', 'Choice 3']);

})();