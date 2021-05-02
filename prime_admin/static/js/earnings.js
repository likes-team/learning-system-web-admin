$(document).ready(function(){

    var table = $('#tbl_members').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "ajax": {
            "url": "/learning-management/dtbl/earnings/members",
            "data": function (d) {
                d.contact_person = $("#btn_marketer_label").val();
                d.branch = $("#branch").val();
                d.batch_no = $("#batch_no").val();
            },
            "dataSrc": function(json){
                var totalEarnings = parseFloat(json.totalEarnings).toFixed(2);

                $("#total_earnings").html("₱" + totalEarnings);
                $("#total_savings").html("₱" + json.totalSavings);
                

                if (json.branchesTotalEarnings.length > 0){
                    var newBranchesTotalEarningsList = '';

                    $("#list_branches_total_earnings").children().remove();
                    
                    for (i=0; i < json.branchesTotalEarnings.length; i++){
                        var totalEarnings = parseFloat(json.branchesTotalEarnings[i]['totalEarnings']).toFixed(2);

                        newBranchesTotalEarningsList = newBranchesTotalEarningsList + `<li class="list-group-item">
                        <div class="widget-content p-0">
                            <div class="widget-content-outer">
                                <div class="widget-content-wrapper">
                                    <div class="widget-content-left">
                                        <div class="widget-heading">${json.branchesTotalEarnings[i]['name']}</div>
                                        <div class="widget-subheading">Total Earnings</div>
                                    </div>
                                    <div class="widget-content-right">
                                        <div class="widget-numbers text-primary">₱ ${totalEarnings}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </li>`
                    }

                    $("#list_branches_total_earnings").html(newBranchesTotalEarningsList);

                    console.log(json.branchesTotalEarnings);
    
                }
         
                return json.data;
            }
        }
    });

    $("#div_marketer_buttons").on('click', '.btn-marketer', function () {
        var marketer_name = $(this).html();

        // if(!(localStorage.getItem('sessSubArea') == _sub_area_name)){
        $("#btn_marketer_label").html(marketer_name.toUpperCase());
        $("#btn_marketer_label").val($(this).val());
        $("#card_header_label").html(marketer_name);

        $('#btn_marketer_label').trigger('change');
        // dtbl_subscribers.ajax.url(`/bds/api/sub-areas/${$(this).val()}/subscribers`).load();
        // }

    });

    $("#btn_marketer_label").change(function(){
        table.ajax.reload();
    });

    $("#branch").change(function(){
        table.ajax.reload();
    });

    $("#batch_no").change(function(){
        table.ajax.reload();
    });
});