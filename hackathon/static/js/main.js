document.addEventListener('DOMContentLoaded', function() {
    // Book page navigation
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    const pageIndicator = document.getElementById('page-indicator');
    
    const themesPage = document.getElementById('themes-page');
    const chaptersPage = document.getElementById('chapters-page');
    const samplePage = document.getElementById('sample-page');
    
    let currentPage = 1;
    const totalPages = 3;
    
    if (prevButton && nextButton && pageIndicator) {
        updatePageControls();
        
        prevButton.addEventListener('click', function() {
            if (currentPage > 1) {
                currentPage--;
                updateBookPages();
                updatePageControls();
            }
        });
        
        nextButton.addEventListener('click', function() {
            if (currentPage < totalPages) {
                currentPage++;
                updateBookPages();
                updatePageControls();
            }
        });
    }
    
    function updateBookPages() {
        if (themesPage && chaptersPage && samplePage) {
            themesPage.style.transform = `translateX(${(1 - currentPage) * 100}%)`;
            chaptersPage.style.transform = `translateX(${(2 - currentPage) * 100}%)`;
            samplePage.style.transform = `translateX(${(3 - currentPage) * 100}%)`;
        }
    }
    
    function updatePageControls() {
        if (prevButton && nextButton && pageIndicator) {
            prevButton.disabled = currentPage === 1;
            nextButton.disabled = currentPage === totalPages;
            pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
        }
    }
    
    // Print functionality
    const printButton = document.getElementById('print-book');
    if (printButton) {
        printButton.addEventListener('click', function() {
            window.print();
        });
    }
});