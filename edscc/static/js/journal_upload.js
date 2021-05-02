$(function () {

    var clear_message = false

    $(".js-upload-files").click(function () {
        $("#fileupload").click();
    });

    $("#fileupload").fileupload({
        dataType: 'json',
        sequentialUploads: true,  /* 1. SEND THE FILES ONE BY ONE */
        start: function (e) {  /* 2. WHEN THE UPLOADING PROCESS STARTS, SHOW THE MODAL */
            $("#modal-progress").modal("show");
            if(!clear_message){
                $("#gallery tbody").html("")
                clear_message = true
            }
        },
        stop: function (e) {  /* 3. WHEN THE UPLOADING PROCESS FINALIZE, HIDE THE MODAL */
            $("#modal-progress").modal("hide");
            // Ensure hide occurs after the fade animation has completed
            setTimeout(function(){$("#modal-progress").modal("hide")}, 1000)
        },
        progressall: function (e, data) {  /* 4. UPDATE THE PROGRESS BAR */
            var progress = parseInt(data.loaded / data.total * 100, 10);
            var strProgress = progress + "%";
            $(".progress-bar").css({"width": strProgress});
            $(".progress-bar").text(strProgress);
        },
        done: function (e, data) {
            $("#gallery tbody").prepend(
                    "<tr><td>" + data.result.name + "</td><td>" + data.result.file_type + "</td><td>" + data.result.size + "</td><td>" + data.result.message + "</tr>"
                );
            if (!data.result.is_valid) {
                toastr.warning(data.result.message);
                console.log('is_valid: ' + data.result.is_valid + ' message: ' + data.result.message);
            }
        }

    });
});
