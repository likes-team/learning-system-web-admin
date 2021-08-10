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
});