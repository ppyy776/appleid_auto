<?php
include("header.php");
$currentuser = new user($_SESSION['user_id']);
?>
<title>账号管理</title>
<div class="container" style="padding-top:70px;">
    <div class="col-md-12 center-block" style="float: none;">
        <div class="table-responsive">
            <a href='account_edit.php?action=add' class='btn btn-secondary'>添加账号</a>
            <table class="table table-striped">
                <thead>
                <tr>
                    <th>账号</th>
                    <th>密码</th>
                    <th>备注</th>
                    <th>上次检查</th>
                    <th>操作</th>
                </tr>
                <script>
                    var clipboard = new ClipboardJS('.btn');

                    function show_Task($taskId) {
                        alert("success", "TaskID: " . $taskId, 2000, "");
                    };

                    function alert_success() {
                        Swal.fire({
                            icon: 'success',
                            title: '提示',
                            text: '复制成功',
                            timer: 1000,
                            timerProgressBar: true
                        });
                    }
                </script>
                </thead>
                <?php
                global $conn;
                $result = $conn->query("SELECT id,username,password,remark,last_check,share_link FROM account WHERE owner = '$currentuser->user_id';");
                if ($result->num_rows > 0) {
                    while ($row = $result->fetch_assoc()) {
                        $resultTask = $conn->query("SELECT id,account_id,check_interval,tgbot_chatid,tgbot_token FROM task WHERE owner = '$currentuser->user_id' AND account_id = '{$row['id']}';");
                        $state = 0;
                        $taskId = 0;
                        while ($rowTask = $resultTask->fetch_assoc()) {
                            if ((time()-strtotime($row['last_check']))> (60 * $rowTask['check_interval'] + 3600)) {
                                $state = 1;
                                $taskId = $rowTask['id'];
                            }
                        }
                        if ($resultTask->num_rows < 1) {
                            $state = 2;
                        }
                        $share_link = "{$Sys_config['apiurl']}/share.php?link={$row['share_link']}";
                        if ($state == 0) {
                            echo "<tr><td>{$row['username']}</td><td>{$row['password']}</td><td>{$row['remark']}</td><td>{$row['last_check']}</td><td> <button id='share_link' class='btn btn-success ' data-clipboard-text='$share_link' onclick='alert_success()'>复制链接</button> <a href='account_edit.php?action=edit&id={$row['id']}' class='btn btn-secondary'>编辑</a> <a href='account_edit.php?action=delete&id={$row['id']}' class='btn btn-success'>删除</a> <button id='share_link' class='btn btn-success ' onclick='alert_success()'>正常</button></td></tr>";
                        }else if ($state == 2) {
                            echo "<tr><td>{$row['username']}</td><td>{$row['password']}</td><td>{$row['remark']}</td><td>{$row['last_check']}</td><td> <button id='share_link' class='btn btn-success ' data-clipboard-text='$share_link' onclick='alert_success()'>复制链接</button> <a href='account_edit.php?action=edit&id={$row['id']}' class='btn btn-secondary'>编辑</a> <a href='account_edit.php?action=delete&id={$row['id']}' class='btn btn-success'>删除</a> <button id='share_link' class='btn btn-danger' onclick='alert_success()'>没有任务</button></td></tr>";
                        }else{
                            echo "<tr><td>{$row['username']}</td><td>{$row['password']}</td><td>{$row['remark']}</td><td>{$row['last_check']}</td><td> <button id='share_link' class='btn btn-success ' data-clipboard-text='$share_link' onclick='alert_success()'>复制链接</button> <a href='account_edit.php?action=edit&id={$row['id']}' class='btn btn-secondary'>编辑</a> <a href='account_edit.php?action=delete&id={$row['id']}' class='btn btn-success'>删除</a> <button id='share_link' class='btn btn-danger' onclick='alert_success()'>{$taskId}</button></td></tr>";
                        }
                    }
                } else {
                    echo "<tr><td colspan='5'>暂无账号</td></tr>";
                }
                ?>
            </table>

        </div>
    </div>
</div>
