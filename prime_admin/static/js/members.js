$(document).ready(function(){
    var table = $('#tbl_members').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "ajax": {
            "url": "/learning-management/dtbl/members",
            "data": function (d) {
                d.branch = $("#branch").val();
                d.batch_no = $("#batch_no").val();
                d.schedule = $("#schedule").val();
            },
            "dataSrc": function(json){
                $("#total_installment").html("₱" + json.totalInstallment);
                $("#total_full_payment").html("₱" + json.totalFullPayment);
                $("#total_payment").html("₱" + json.totalPayment);
                $("#sales_today").html("₱" + json.salesToday);

                return json.data;
            }
        }
    });


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
