function show_avatar(avatar_url){
    $('#user_data').empty()
    $('#user_data').append($('<img />').attr('src', avatar_url));
}