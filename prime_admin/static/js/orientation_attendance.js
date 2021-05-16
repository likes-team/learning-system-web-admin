$(document).ready(function(){

    var dtbl_search = $("#tbl_mdl_clients").DataTable({
        pageLength: 10,
        columnDefs: [
            {
                "targets": 0,
                "visible": false,
            },
        ],
        ajax: {
            url: "/learning-management/api/dtbl/mdl-pre-registered-clients",
        }
    });

    $('#tbl_mdl_clients tbody').on( 'click', 'tr', function () {
        if ( $(this).hasClass('selected') ) {
            $(this).removeClass('selected');
        }
        else {
            dtbl_search.$('tr.selected').removeClass('selected');
            $(this).addClass('selected');
        }
    } );


    $('#btn_confirm').click( function () {
        var selected = dtbl_search.row('.selected').data();
        
        $.ajax({
            url: '/learning-management/api/clients/' + selected[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                console.log(response.data);
                
                $("#client_id").val(selected[0]);
                $("#lname").val(selected[1]);
                $("#fname").val(selected[2]);
                $("#contact_no").val(selected[5]);
                $("#contact_person").val(response.data.contact_person);
        
                $("#lname").prop('readonly', true);
                $("#fname").prop('readonly', true);
                $("#contact_no").prop('readonly', true);
                
                if(response.data.status != "pre_registered"){
                    $("#contact_person").prop('disabled', true);
                }
            }
        });


    });

    $('#btn_clear_entries').click( function () {
        $("#client_id").val('');
        $("#lname").val('');
        $("#fname").val('');
        $("#contact_no").val('');
        $("#contact_person").val('');

        $("#lname").prop('readonly', false);
        $("#fname").prop('readonly', false);
        $("#contact_no").prop('readonly', false);
        $("#contact_person").prop('disabled', false);
    });
});