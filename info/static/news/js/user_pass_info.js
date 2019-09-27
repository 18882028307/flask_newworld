function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pass_info").submit(function (e) {
        // 阻止默认事件
        e.preventDefault();
        // TODO 修改密码
        var params = {}
        $(this).serializeArray().map(function (x) {
            alert(x.name)
            params[x.name] = x.value;9
        });
        // 取到两次密码进行判断
        var new_password = params['new_password'];
        var new_password2 = params['new_password2'];
        if (new_password != new_password2){
            alert('两次密码不一致')
            return;
        }
        $.ajax({
            url: '/user/pass_info',
            type: 'post',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCookie('csrf_token')
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == '0'){
                    // 修改成功
                    alert("修改成功")
                    parent.location.reload()
                }else {
                    alert(resp.errmsg)
                }
            }
        })

    })
})