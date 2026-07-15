const SwalConfig = {
    confirmButtonColor: '#00897b',
    cancelButtonColor: '#78909c',
    customClass: { popup: 'swal2-popup-custom' },
    font: "'Inter', sans-serif"
};

function swalSuccess(title, text = '') {
    return Swal.fire({
        ...SwalConfig,
        icon: 'success',
        title: title,
        text: text,
        showConfirmButton: false,
        timer: 2500,
        timerProgressBar: true
    });
}

function swalError(title, text = '') {
    return Swal.fire({
        ...SwalConfig,
        icon: 'error',
        title: title,
        text: text,
        confirmButtonText: 'Entendido'
    });
}

function swalWarning(title, text = '') {
    return Swal.fire({
        ...SwalConfig,
        icon: 'warning',
        title: title,
        text: text,
        confirmButtonText: 'OK'
    });
}

function swalInfo(title, text = '') {
    return Swal.fire({
        ...SwalConfig,
        icon: 'info',
        title: title,
        text: text,
        confirmButtonText: 'Entendido'
    });
}

function swalConfirm(title, text = '', confirmText = 'Sí, eliminar') {
    return Swal.fire({
        ...SwalConfig,
        icon: 'question',
        title: title,
        text: text,
        showCancelButton: true,
        confirmButtonColor: '#ef5350',
        cancelButtonColor: '#78909c',
        confirmButtonText: confirmText,
        cancelButtonText: 'Cancelar'
    });
}

function swalConfirmDanger(title, text = '') {
    return Swal.fire({
        ...SwalConfig,
        icon: 'warning',
        title: title,
        text: text,
        showCancelButton: true,
        confirmButtonColor: '#ef5350',
        cancelButtonColor: '#78909c',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        customClass: { popup: 'swal2-popup-custom swal2-danger' }
    });
}

function swalLoading(title = 'Cargando...') {
    return Swal.fire({
        ...SwalConfig,
        title: title,
        allowOutsideClick: false,
        allowEscapeKey: false,
        didOpen: () => { Swal.showLoading(); }
    });
}

function swalClose() {
    Swal.close();
}

function swalToast(icon, title) {
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.onmouseenter = Swal.stopTimer;
            toast.onmouseleave = Swal.resumeTimer;
        }
    });
    return Toast.fire({ icon, title });
}
