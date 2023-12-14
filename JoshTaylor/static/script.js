document.addEventListener('DOMContentLoaded', function() {
    const tooltips = document.querySelectorAll('.text-with-tooltip');
    tooltips.forEach(t=> {
        
        new bootstrap.Tooltip(t);
    });
});

document.addEventListener('DOMContentLoaded', function(){
    const text = document.querySelector('#logo');
    let isUnderlined = true;
    setInterval(function() {
        if (isUnderlined){
            text.classList.remove('underlined');
        } else {
            text.classList.add('underlined');
        }
        isUnderlined = !isUnderlined;
        }, 500)
    });

