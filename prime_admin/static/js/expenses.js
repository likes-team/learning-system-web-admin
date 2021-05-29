$(document).ready(function(){
    var table = $('#tbl_expenses').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "ajax": {
            "url": "/learning-management/dtbl/expenses",
            "data": function (d) {
                d.branch = $("#btn_branch_label").val();
                d.description = $("#description").val();
            },
            "dataSrc": function(json){
                // $("#total_payment").html("₱" + json.totalPayment + ".00");
                $("#expenses_today").html("₱" + json.expensesToday + ".00");
                $("#total").val(json.total);

                return json.data;
            }
        }
    });

    $("#div_branches_buttons").on('click', '.btn-branch', function () {
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
        table.ajax.reload();
    });

    $("#description").change(function(){
        table.ajax.reload();
    });

});
