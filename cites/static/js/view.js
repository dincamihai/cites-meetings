(function ($, app) {

$(function () {
    $(".modal").on("click", ".btn-cancel", function () {
        $(".modal").modal("hide");
    });

    $("#delete-modal").on("click", ".btn-primary", function () {
        $.ajax({
            type: "DELETE",
            url: "/meeting/1/participant/" + $(this).data("id")
        }).done(function () {
            document.location = "{{ url_for('meeting.registration') }}";
        });
    });

    $("input[type=file]").uniform();
    $("#participant-upload-photo").on("click", function (e) {
        e.preventDefault();
        $("#file-input-container").slideToggle("fast");
    });

    // form events
    $("#file-input-container").on("change", "input[type=file]", function () {
        var form = $(this).parents("form");
        form.submit();
    });

    // iframe events
    $("#file-input-iframe").load(function () {
        // after the upload is complete update the picture with the new one
        var data = $.parseJSON($(this).contents().text());

        if(data && data.status == "success") {
           $("#file-input-container").slideUp("fast");
           $("#participant-photo").find("img").fadeOut("slow", function () {
               data.url += "?" + new Date().getTime();
               $(this).attr("src", data.url).fadeIn("slow");
           });
        }
    });
});

})($, app);
