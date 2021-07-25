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

    var dtbl_user_status = $('#tbl_user_status').DataTable({
        "dom": 'rtip',
        "pageLength": 20,
        "order": [[ 1, 'asc' ]],
        "processing": true,
        "serverSide": true,
        "autoWidth": false,
        "ajax": {
            "url": "/admin/dashboard/get-dashboard-users", // To be continued
        },
        "columnDefs": [
            {
                "targets": 0,
                "className": "text-center text-muted",
                "width": "10px"
            },
            {
                "targets": 1,
                "className": "text-center",
            },
            {
                "targets": 2,
                "render": function(data, type, row){
                    return `<td>
                        <div class="widget-content p-0">
                            <div class="widget-content-wrapper">
                                <div class="widget-content-left mr-3">
                                    <div class="widget-content-left">
                                        <img width="40" class="rounded-circle" src="/auth/auth/static/img/user_default_image.png" alt=""></div>
                                </div>
                                <div class="widget-content-left flex2">
                                    <div class="widget-heading">${data['name']}</div>
                                    <div class="widget-subheading opacity-7">${data['username']}</div>
                                </div>
                            </div>
                        </div>
                    </td>`;
                }
            },
            {
                "targets": 3,
                "className": "text-center",
            },
            {
                "targets": 4,
                "className": "text-center",
                "render": function(data, type, row){
                    if(data){
                        return `<div class="badge badge-success">Approved</div>`
                    }
                    return `<div class="badge badge-danger">Not Approved</div>`
                }
            },
            {
                "targets": 5,
                "className": "text-center",
                "render": function(data, type, row){
                    if(!data){
                        return `
                        <button type="button" class="btn btn-primary btn-sm btn-approve">Approve</button>
                        `
                    }
                    return `
                    <div></div>
                    ` 
                }
            },
        ],
    });

    $("#tbl_user_status tbody").on('click', '.btn-approve', function(){
        var data = dtbl_user_status.row( $(this).parents('tr')).data();
        
        console.log(data[0]);

        $.confirm({
            title: 'User Approval',
            content: 'Approve user?',
            buttons: {
                confirm: {
                    text: 'Approve',
                    btnClass: 'btn-blue',
                    keys: ['enter', 'shift'],
                    action: function(){
                        console.log(data[0]);

                        $.ajax({
                            url: "/admin/dashboard/approve-user",
                            type: "POST",
                            dataType: "json",
                            data: JSON.stringify({
                                "user_id": data[0]
                            }),
                            contentType: "application/json; charset=utf-8",
                            success: function(response){
                                if(response){
                                    dtbl_user_status.ajax.reload();
                                    toastr.success("User Approved Successfully!");
                                }else{
                                    toastr.error("Error Occured!, Approving Failed");
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