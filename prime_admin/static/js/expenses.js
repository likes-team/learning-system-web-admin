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
                d.description = $("#description").val();
            },
            "dataSrc": function(json){
                // $("#total_installment").html("₱" + json.totalInstallment + ".00");
                // $("#total_full_payment").html("₱" + json.totalFullPayment + ".00");
                // $("#total_payment").html("₱" + json.totalPayment + ".00");
                // $("#sales_today").html("₱" + json.salesToday + ".00");

                return json.data;
            }
        }
    });

    $("#description").change(function(){
        table.ajax.reload();
    });

});
