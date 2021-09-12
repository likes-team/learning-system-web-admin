$(document).ready(function(){
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            }
        }
    });

    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": false,
        "positionClass": "toast-top-center",
        "preventDuplicates": false,
        "onclick": null,
        "showDuration": "3000",
        "hideDuration": "1000",
        "timeOut": "5000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
        }


    var table = $('#tbl_members').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "processing": true,
        "serverSide": true,
        "columnDefs": [
            { className: "text-center", "targets": [ 9, 10 ] },
            {visible: false, targets:[0,1,3]}
        ],
        ordering: false,
        "order": [[ 3, 'asc' ]],
        "drawCallback": function ( settings ) {
            var api = this.api();
            var rows = api.rows( {page:'current'} ).nodes();
            var last=null;
 
            api.column(3, {page:'current'} ).data().each( function ( group, i ) {
                if ( last !== group ) {
                    $(rows).eq( i ).before(
                        '<tr style="background-color: lightcyan !important"><td colspan="9"><strong>'+group+' Payments:</strong></td></tr>'
                    );
 
                    last = group;
                }
            } );
        },
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
                $("#total_earnings_claimed").html("₱" + json.totalEarningsClaimed);
                $("#total_savings_claimed").html("₱" + json.totalSavingsClaimed);

                $("#list_branches_total_earnings").children().remove();

                if (json.branchesTotalEarnings.length > 0){
                    var newBranchesTotalEarningsList = '';
                    
                    for (i=0; i < json.branchesTotalEarnings.length; i++){
                        var totalEarnings = parseFloat(json.branchesTotalEarnings[i]['totalEarnings']).toFixed(2);

                        newBranchesTotalEarningsList = newBranchesTotalEarningsList + `<li class="list-group-item">
                        <div class="widget-content p-0">
                            <div class="widget-content-outer">
                                <div class="widget-content-wrapper">
                                    <div class="widget-content-left">
                                        <div class="widget-heading">${json.branchesTotalEarnings[i]['name']}</div>
                                        <div class="widget-subheading">Current Earnings</div>
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

    var dtbl_transaction_history = $('#tbl_transaction_history').DataTable({
        "dom": 'rtip',
        "pageLength": 25,
        "processing": true,
        "order": [[1, 'asc']],
        "ordering": false,
        "ajax": {
            "url": "/learning-management/api/get-earning-transaction-history",
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
        getProfitSharingEarnings();
    });

    $("#branch").change(function(){
        
        $.ajax({
            url: `/learning-management/api/branches/${$(this).val()}/batches`,
                type: "GET",
                contentType: "application/json; charset=utf-8",
                success: function(response) {
                    $('#batch_no').find('option').remove();
    
                    if (response.data.length > 0) {
                        var newOption = $('<option value="all">All</option>');
                        $('#batch_no').append(newOption);
    
                        for (i = 0; i < response.data.length; i++) {
                            var newOption = $(`<option value="${response.data[i].id}">${response.data[i].number}</option>`);
                            $('#batch_no').append(newOption);
                        }
                    } else {
                        var newOption = $('<option value="all">No batch number available</option>');
                        $('#batch_no').append(newOption);
                    }
                }
            });
        table.ajax.reload();
    });

    $("#batch_no").change(function(){
        table.ajax.reload();
    });

    $("#tbl_members tbody").on('click', '.btn-claim', function(){
        var data = table.row( $(this).parents('tr')).data();
        
        $.confirm({
            title: 'Request for claim',
            content: `Php ${data[5] + data[6]}`,
            buttons: {
                confirm: {
                    text: 'Request',
                    btnClass: 'btn-blue',
                    keys: ['enter', 'shift'],
                    action: function(){
                        $.ajax({
                            url: "/learning-management/api/claim-earning",
                            type: "POST",
                            dataType: "json",
                            data: JSON.stringify({
                                "student_id": data[0],
                                "payment_id": data[1]
                            }),
                            contentType: "application/json; charset=utf-8",
                            success: function(response){
                                if(response.result){
                                    table.ajax.reload();
                                    toastr.success("Wait for admin to approve","Claim successfully requested!");
                                }else{
                                    toastr.error("Requesting claim Failed", "Error Occured!");
                                }
                            }
                        });
                    }
                },
                cancel: function () {
                    $.alert('Canceled!');
                },
            }
        });
    });

    $("#tbl_members tbody").on('click', '.btn-approve-claim', function(){
        var data = table.row( $(this).parents('tr')).data();
        var marketer = $("#card_header_label").text();
        var marketer_id = $("#btn_marketer_label").val();

        $.confirm({
            title: `Approve ${marketer}'s claim`,
            content: `Php ${data[5] + data[6]}`,
            buttons: {
                confirm: {
                    text: 'Approve',
                    btnClass: 'btn-blue',
                    keys: ['enter', 'shift'],
                    action: function(){
                        $.ajax({
                            url: "/learning-management/api/approve-claim-earning",
                            type: "POST",
                            dataType: "json",
                            data: JSON.stringify({
                                "student_id": data[0],
                                "payment_id": data[1],
                                'marketer_id': marketer_id
                            }),
                            contentType: "application/json; charset=utf-8",
                            success: function(response){
                                if(response.result){
                                    table.ajax.reload();
                                    dtbl_transaction_history.reload();
                                    toastr.success("Marketers request claim","Claim request successfully approved!");
                                }else{
                                    toastr.error("Approving claim request failed", "Error Occured!");
                                }
                            }
                        });
                    }
                },
                cancel: function () {
                    $.alert('Canceled!');
                },
            }
        });
    });



    getProfitSharingEarnings();
});

function getProfitSharingEarnings(){
    var partner_id = $("#btn_marketer_label").val();

    $.ajax({
        url: "/learning-management/api/get-profit-sharing-earnings/" + partner_id,
        type: "GET",
        contentType: "application/json; charset=utf-8",
        success: function(response){
            if(response.result){
                $("#total_earnings_profit").html("₱" + response.totalEarningsProfit);

                $("#list_branches_total_earnings_profit").children().remove();

                if (response.branchesTotalEarningsProfit.length > 0){
                    var newBranchesTotalEarningsList = '';
                    
                    for (i=0; i < response.branchesTotalEarningsProfit.length; i++){
                        var totalEarnings = parseFloat(response.branchesTotalEarningsProfit[i]['totalEarnings']).toFixed(2);

                        newBranchesTotalEarningsList = newBranchesTotalEarningsList + `<li class="list-group-item">
                        <div class="widget-content p-0">
                            <div class="widget-content-outer">
                                <div class="widget-content-wrapper">
                                    <div class="widget-content-left">
                                        <div class="widget-heading">${response.branchesTotalEarningsProfit[i]['name']}</div>
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

                    $("#list_branches_total_earnings_profit").html(newBranchesTotalEarningsList);
                }
            }else{
            }
        }
    });
}