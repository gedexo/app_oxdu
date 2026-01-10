(function () {
    "use strict"

    const pickrContainer1 = document.querySelector('.pickr-container1');
    const themeContainer1 = document.querySelector('.theme-container1');

    /* monolith */
    const monolithThemes = [
        [
            'monolith',
            {
                swatches: [
                    'rgba(244, 67, 54, 1)',
                    'rgba(233, 30, 99, 0.95)',
                    'rgba(156, 39, 176, 0.9)',
                    'rgba(103, 58, 183, 0.85)',
                    'rgba(63, 81, 181, 0.8)',
                    'rgba(33, 150, 243, 0.75)',
                    'rgba(3, 169, 244, 0.7)'
                ],

                defaultRepresentation: 'HEXA',
                components: {
                    preview: true,
                    opacity: true,
                    hue: true,

                    interaction: {
                        hex: false,
                        rgba: false,
                        hsva: false,
                        input: true,
                        clear: true,
                        save: true
                    }
                }
            }
        ]
    ];

    const monolithButtons = [];
    let monolithPickr = null;

    for (const [theme, config] of monolithThemes) {
        const button = document.createElement('button');
        button.innerHTML = theme;
        monolithButtons.push(button);

        button.addEventListener('click', () => {
            const el = document.createElement('p');
            pickrContainer1.appendChild(el);

            /* Delete previous instance */
            if (monolithPickr) {
                monolithPickr.destroyAndRemove();
            }

            /* Apply active class */
            for (const btn of monolithButtons) {
                btn.classList[btn === button ? 'add' : 'remove']('active');
            }

            /* Create fresh instance */
            monolithPickr = new Pickr(Object.assign({
                el,
                theme,
                default: '#fc5296'
            }, config));

            /* Set events */
            monolithPickr.on('init', instance => {
                // console.log('Event: "init"', instance);
            }).on('hide', instance => {
                // console.log('Event: "hide"', instance);
            }).on('show', (color, instance) => {
                // console.log('Event: "show"', color, instance);
            }).on('save', (color, instance) => {
                // console.log('Event: "save"', color, instance);
            }).on('clear', instance => {
                // console.log('Event: "clear"', instance);
            }).on('change', (color, source, instance) => {
                // console.log('Event: "change"', color, source, instance);
            }).on('changestop', (source, instance) => {
                // console.log('Event: "changestop"', source, instance);
            }).on('cancel', instance => {
                // console.log('cancel', monolithPickr.getColor().toRGBA().toString(0));
            }).on('swatchselect', (color, instance) => {
                // console.log('Event: "swatchselect"', color, instance);
            });
        });

        themeContainer1.appendChild(button);
    }

    monolithButtons[0].click();
    
    /* For Time Picker1 */
     flatpickr("#choose-time1", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
    });
    /* For Time Picker2 */
    flatpickr("#choose-time2", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
    });
     
})();