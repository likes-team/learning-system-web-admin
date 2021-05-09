$(document).ready(function(){
    var BATCHID;
    var ROWSTATUS;

    $("#index_table tbody").on('click','.row_object',function(){

        var $row = $(this).closest('tr');

        // Get row data
        var data = dtbl_table.row($row).data();

        BATCHID = data.DT_RowId;

        var row_status = data[1];

        if(row_status == `<div class="mb-2 mr-2 badge badge-pill badge-success">ACTIVE</div>`){
            ROWSTATUS = 0;
            $("#btn_active_toggle").html('Set Inactive');
            $("#btn_active_toggle").removeClass("btn-success").addClass("btn-secondary");
        } else {
            ROWSTATUS = 1;
            $("#btn_active_toggle").html('Set Active');
            $("#btn_active_toggle").removeClass("btn-secondary").addClass("btn-success");
        }
    
    });


    $("#btn_active_toggle").click(function(){
        const url = "/learning-management/batches/" + BATCHID + "/set-active";

        $.ajax({
            url: url,
            type: "POST",
            dataType: "json",
            data: JSON.stringify({
                'status': ROWSTATUS,
            }),
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                if (data.result) {
                    location.reload();

                    if(ROWSTATUS){
                        $("#btn_active_toggle").html('Set Inactive');
                        $("#btn_active_toggle").removeClass("btn-success").addClass("btn-secondary");
                    } else {
                        $("#btn_active_toggle").html('Set Active');
                        $("#btn_active_toggle").removeClass("btn-secondary").addClass("btn-success");
                    }
                }
            }
        });
    });

});