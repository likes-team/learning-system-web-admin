$(document).ready(function(){
    var table = $('#tbl_members').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "autoWidth": false,
        "columnDefs": [
            { "visible": false, "targets": 0},
            { "width": 100, "targets": 15},
            { "width": "10px", "targets": 12}
        ],
        "ajax": {
            "url": "/learning-management/dtbl/members",
            "data": function (d) {
                d.branch = $("#branch").val();
                d.batch_no = $("#batch_no").val();
                d.schedule = $("#schedule").val();
            },
            "dataSrc": function(json){
                $("#total_installment").html("₱" + json.totalInstallment + ".00");
                $("#total_full_payment").html("₱" + json.totalFullPayment + ".00");
                $("#total_payment").html("₱" + json.totalPayment + ".00");
                $("#sales_today").html("₱" + json.salesToday + ".00");

                return json.data;
            }
        }
    });

    // $('#tbl_members tbody').on('click', 'tr', function () {
    //     var data = table.row( this ).data();
        
    //     $("#viewModal").modal('toogle');
    //     $("#viewModal").modal('show');
    // } );

    
    $('#tbl_members tbody').on('click', '.btn-edit', function () {
        var data = table.row( $(this).parents('tr') ).data();
        
        console.log(data);
        $.ajax({
            url: '/learning-management/api/members/' + data[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                console.log(response.data);
                
                $("#client_id").val(response.data.id);
                $("#edit_last_name").val(response.data.lname);
                $("#edit_first_name").val(response.data.fname);
                $("#edit_middle_name").val(response.data.mname);
                $("#edit_suffix").val(response.data.suffix);
                $("#edit_mode_of_payment").val(response.data.mode_of_payment);
                $("#edit_amount").val(response.data.amount);
                $("#edit_balance").val(response.data.balance);
            }
        });
    } );
        
    $('#tbl_members tbody').on('click', '.btn-view', function () {
        var data = table.row( $(this).parents('tr') ).data();
        
        console.log(data);
        $.ajax({
            url: '/learning-management/api/members/' + data[0],
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function(response) {
                console.log(response.data);
                
                // $("#client_id").val(selected[0]);
                $("#view_last_name").val(response.data.lname);
                $("#view_first_name").val(response.data.fname);
                $("#view_middle_name").val(response.data.mname);
                $("#view_suffix").val(response.data.suffix);
                $("#view_batch_no").val(response.data.batch_no);
                $("#view_schedule").val(response.data.schedule);
                $("#view_branch").val(response.data.branch);
                $("#view_contact_person").val(response.data.contact_person);
                $("#view_date_of_birth").val(response.data.birth_date);
                $("#view_passport").val(response.data.passport);
                $("#view_contact_no").val(response.data.contact_no);
                $("#view_email").val(response.data.email);
                $("#view_address").val(response.data.address);
                $("#view_mode_of_payment").val(response.data.mode_of_payment);
                $("#view_book").val(response.data.book);
                $("#view_uniform").val(response.data.uniform);
                $("#view_amount").val(response.data.amount);
                $("#view_balance").val(response.data.balance);
            }
        });

    } );

    $("#branch").change(function(){
        table.ajax.reload();
    });

    $("#batch_no").change(function(){
        table.ajax.reload();
    });

    $("#schedule").change(function(){
        table.ajax.reload();
    });
});
