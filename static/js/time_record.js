$(document).ready(function() {
    $('form').on('submit', function(e) {
        e.preventDefault(); // Prevent page reload
        const url = $(this).data('url');
        $.ajax({
            url: url,
            type: 'GET',
            data: $(this).serialize(), // Get form data
            success: function(response) {
                // Update the table body with the new content
                $('table tbody').html(response.table_html);
            },
            error: function(_xhr, _status, error) {
                console.error('AJAX Error:', error);
            }
        });
    });
});