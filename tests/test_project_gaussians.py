import pytest
import torch


device = torch.device("cuda:0")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="No CUDA device")
def test_project_gaussians_forward():
    from gsplat import _torch_impl
    import gsplat.cuda as _C

    torch.manual_seed(42)

    num_points = 100

    means3d = torch.randn((num_points, 3), device=device, requires_grad=True)
    scales = torch.randn((num_points, 3), device=device)
    glob_scale = 0.3
    quats = torch.randn((num_points, 4), device=device)
    quats /= torch.linalg.norm(quats, dim=-1, keepdim=True)
    # TODO: test with non-identity viewmat and projmat
    viewmat = torch.eye(4, device=device)
    projmat = torch.eye(4, device=device)
    fullmat = projmat @ viewmat
    H, W = 512, 512
    cx, cy = W / 2, H / 2
    # 90 degree FOV
    fx, fy = W / 2, W / 2
    clip_thresh = 0.01

    BLOCK_X, BLOCK_Y = 16, 16
    tile_bounds = (W + BLOCK_X - 1) // BLOCK_X, (H + BLOCK_Y - 1) // BLOCK_Y, 1

    (
        cov3d,
        xys,
        depths,
        radii,
        conics,
        num_tiles_hit,
    ) = _C.project_gaussians_forward(
        num_points,
        means3d,
        scales,
        glob_scale,
        quats,
        viewmat,
        fullmat,
        fx,
        fy,
        cx,
        cy,
        H,
        W,
        tile_bounds,
        clip_thresh,
    )
    masks = radii > 0

    (
        _cov3d,
        _xys,
        _depths,
        _radii,
        _conics,
        _num_tiles_hit,
        _masks,
    ) = _torch_impl.project_gaussians_forward(
        means3d,
        scales,
        glob_scale,
        quats,
        viewmat,
        fullmat,
        (fx, fy, cx, cy),
        (W, H),
        tile_bounds,
        clip_thresh,
    )

    torch.testing.assert_close(masks, _masks, atol=1e-5, rtol=1e-5)
    torch.testing.assert_close(
        cov3d[_masks],
        _cov3d[_masks],
        atol=1e-5,
        rtol=1e-5,
    )
    torch.testing.assert_close(
        xys[_masks],
        _xys[_masks],
        atol=1e-5,
        rtol=1e-5,
    )
    torch.testing.assert_close(depths[_masks], _depths[_masks])
    torch.testing.assert_close(radii[_masks], _radii[_masks])
    torch.testing.assert_close(conics[_masks], _conics[_masks])
    torch.testing.assert_close(num_tiles_hit[_masks], _num_tiles_hit[_masks])
    print("passed project_gaussians_forward test")


if __name__ == "__main__":
    test_project_gaussians_forward()
