// Show comment form at click location
function showCommentForm(event) {
    const img = event.target;
    const rect = img.getBoundingClientRect();
    const x = Math.round(event.clientX - rect.left);
    const y = Math.round(event.clientY - rect.top);
    // Try to get name from cookie
    let commenterName = '';
    document.cookie.split(';').forEach(function (c) {
        if (c.trim().startsWith('commorg_name=')) {
            commenterName = decodeURIComponent(c.trim().substring('commorg_name='.length));
        }
    });
    const formHtml = `
<form method="post" class="commorg-comment-form">
  ${window.csrf_token_html || ''}
  <input type="hidden" name="x" value="${x}" />
  <input type="hidden" name="y" value="${y}" />
  <label>Name: <input type="text" name="commenter_name" value="${commenterName}" required /></label><br>
  <label>Comment:<br><textarea name="content" required style="width: 100%;"></textarea></label><br>
  <button type="submit" name="add_comment">Add Comment at (${x}, ${y})</button>
  <button type="button" onclick="document.getElementById('comment-form-container').style.display='none';">Cancel</button>
</form>
`;
    const container = document.getElementById('comment-form-container');
    container.innerHTML = formHtml;
    container.style.display = 'block';
    window.scrollTo({ top: container.offsetTop - 100, behavior: 'smooth' });
}

// Save name to cookie on submit
function commorgSetupCommentCookie() {
    document.addEventListener('submit', function (e) {
        if (e.target && e.target.querySelector('input[name="commenter_name"]')) {
            const name = e.target.querySelector('input[name="commenter_name"]').value;
            document.cookie = 'commorg_name=' + encodeURIComponent(name) + ';path=/;max-age=31536000';
        }
    });
}

// Acknowledge button logic
function getCookieName() {
    let name = '';
    document.cookie.split(';').forEach(function (c) {
        if (c.trim().startsWith('commorg_name=')) {
            name = decodeURIComponent(c.trim().substring('commorg_name='.length));
        }
    });
    return name;
}
function setCookieName(name) {
    document.cookie = 'commorg_name=' + encodeURIComponent(name) + ';path=/;max-age=31536000';
}
function updateAcknowledgeBtn() {
    const name = getCookieName();
    const btn = document.getElementById('acknowledge-btn');
    if (btn) {
        if (name) {
            btn.textContent = 'Acknowledge as ' + name;
        } else {
            btn.textContent = 'Click to Acknowledge';
        }
    }
}

function commorgSetupAcknowledgeBtn() {
    updateAcknowledgeBtn();
    const btn = document.getElementById('acknowledge-btn');
    if (btn) {
        btn.onclick = function () {
            let name = getCookieName();
            if (!name) {
                name = prompt('Enter your name to acknowledge this draft:');
                if (!name) return;
                setCookieName(name);
                updateAcknowledgeBtn();
            }
            // Set name in hidden form and submit
            document.getElementById('acknowledge-name-input').value = name;
            document.getElementById('acknowledge-form').submit();
        };
    }
}

document.addEventListener('DOMContentLoaded', function () {
    commorgSetupCommentCookie();
    commorgSetupAcknowledgeBtn();
}); 