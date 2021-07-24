$(document).ready(function(){
    var dtbl_statement = $('#tbl_statement').DataTable({
        "dom": 'rtip',
        "pageLength": 100,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "columnDefs": [
            { "visible": false, "targets": 8 }
        ],
        "ajax": {
            "url": "/learning-management/dtbl/get-cash-flow",
            "data": function (d) {
                d.branch = $("#btn_branch_label").val();
                d.from_what = "sales"
            },
            "dataSrc": function(json){
                var remaining = parseFloat(json.remaining).toFixed(2);
                var net = parseFloat(json.net).toFixed(2);
                var fund1 = parseFloat(json.fund1).toFixed(2);
                var fund2 = parseFloat(json.fund2).toFixed(2);

                $("#total_gross_sales").html("₱" + json.totalGrossSales);
                $("#remaining").html("₱" + remaining);
                $("#net").html("₱" + net);
                $("#fund1").html("₱" + fund1);
                $("#fund2").html("₱" + fund2);
                $("#final_fund1").html("₱" + json.finalFund1);
                $("#final_fund2").html("₱" + json.finalFund2);  
                return json.data;
            }
        }
    });

    var dtbl_fund_statement = $('#tbl_fund_statement').DataTable({
        "dom": 'rtip',
        "pageLength": 100,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "columnDefs": [
            { "visible": false, "targets": 8 }
        ],
        "ajax": {
            "url": "/learning-management/dtbl/get-cash-flow",
            "data": function (d) {
                d.branch = $("#btn_branch_label").val();
                d.from_what = "fund"
            },
            "dataSrc": function(json){
                var remaining = parseFloat(json.remaining).toFixed(2);
                var net = parseFloat(json.net).toFixed(2);
                var fund1 = parseFloat(json.fund1).toFixed(2);
                var fund2 = parseFloat(json.fund2).toFixed(2);

                $("#total_gross_sales").html("₱" + json.totalGrossSales);
                $("#remaining").html("₱" + remaining);
                $("#net").html("₱" + net);
                $("#fund1").html("₱" + fund1);
                $("#fund2").html("₱" + fund2);
                $("#final_fund1").html("₱" + json.finalFund1);
                $("#final_fund2").html("₱" + json.finalFund2);  
                return json.data;
            }
        }
    });

    $("#div_branch_buttons").on('click', '.btn-branch', function () {
        var branch_name = $(this).html();

        // if(!(localStorage.getItem('sessSubArea') == _sub_area_name)){
        $("#btn_branch_label").html(branch_name.toUpperCase());
        $("#btn_branch_label").val($(this).val());
        $("#card_header_label").html(branch_name);

        $('#btn_branch_label').trigger('change');
        // dtbl_subscribers.ajax.url(`/bds/api/sub-areas/${$(this).val()}/subscribers`).load();
        // }

    });

    $("#btn_branch_label").change(function(){
        dtbl_statement.ajax.reload();
        dtbl_fund_statement.ajax.reload();
    });

    // $("#branch").change(function(){
    //     dtbl_statement.ajax.reload();
    // });

    // $("#batch_no").change(function(){
    //     dtbl_statement.ajax.reload();
    // });

    // $("#btn_deposit").click(function(){

    //     $.confirm({
    //         title: 'Deposit',
    //         content: 'Confirm?',
    //         buttons: {
    //             confirm: {
    //                 text: 'Confirm',
    //                 btnClass: 'btn-blue',
    //                 keys: ['enter', 'shift'],
    //                 action: function(){
    //                     document.frm_deposit.submit();
    //                 }
    //             },
    //             cancel: function () {
    //                 $.alert('Canceled!');
    //             },
    //         }
    //     });
    // });
});