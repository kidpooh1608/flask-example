$(document).ready(function(){
    $('form#task_history').submit(function(event) {
        $.ajax({
            type        : 'GET', 
            url         : 'http://localhost:8976/clear-history',
            dataType    : 'json',
            contentType: false,
            processData: false
        })

        .done(function(data) {
            if (data != 'OK') {
                swal('Oops', "history was not cleared", "error");
           }
        });

        event.preventDefault();
        var body = '';
        $('tbody#tasks_record').html(body);
    });
});