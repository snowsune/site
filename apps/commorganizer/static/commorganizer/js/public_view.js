// Vixi wrote this! Dont yell at me!

// Position makers!
function positionMarkers() {
    // Get the image
    const img = document.getElementById('main-draft-img');

    // Oops :P
    if (!img || !img.complete) return;

    // Get the natural width and height
    const naturalWidth = img.naturalWidth;
    const naturalHeight = img.naturalHeight;

    // Get the markers
    const markers = document.querySelectorAll('.comment-marker');

    // For each marker, get x and y
    markers.forEach(marker => {
        const x = parseInt(marker.getAttribute('data-x'));
        const y = parseInt(marker.getAttribute('data-y'));

        // Calculate percentage position relative to natural image size
        const xPercent = (x / naturalWidth) * 100;
        const yPercent = (y / naturalHeight) * 100;

        // Position using percentages so they scale with the image
        marker.style.left = xPercent + '%';
        marker.style.top = yPercent + '%';
    });
}

// This is so you can toggle on and off the annotations!
function toggleAnnotations() {
    const markers = document.querySelectorAll('.comment-marker');
    const btn = document.getElementById('toggle-annotations-btn'); // the template adds this
    const isHidden = markers[0]?.classList.contains('hidden');

    // For each marker, add or remove the hidden class
    markers.forEach(marker => {
        if (isHidden) {
            marker.classList.remove('hidden');
        } else {
            marker.classList.add('hidden');
        }
    });

    // If the button exists, change the text and add or remove the annotations-hidden class
    if (btn) {
        if (isHidden) {
            btn.textContent = 'Hide Annotations';
            btn.classList.remove('annotations-hidden');
        } else {
            btn.textContent = 'Show Annotations';
            btn.classList.add('annotations-hidden');
        }
    }
}

// Show comment form at click location
function showCommentForm(event) {
    const img = event.target;
    const rect = img.getBoundingClientRect();

    // Calculate position relative to the displayed image
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    // Convert to natural image coordinates
    const scaleX = img.naturalWidth / rect.width;
    const scaleY = img.naturalHeight / rect.height;
    const x = Math.round(clickX * scaleX);
    const y = Math.round(clickY * scaleY);

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
  <button type="submit" name="add_comment">Add Comment${x !== 0 || y !== 0 ? ` at (${x}, ${y})` : ''}</button>
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

    // Position markers when image loads
    const img = document.getElementById('main-draft-img');
    if (img) {
        if (img.complete) {
            positionMarkers();
        } else {
            img.addEventListener('load', positionMarkers);
        }

        // Reposition markers on window resize
        window.addEventListener('resize', positionMarkers);
    }
}); 