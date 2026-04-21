from typing import Any

from fastapi import APIRouter, Query

from ..modules import network as mnetwork

router = APIRouter()


@router.get("/network/dns", tags=["Network"])
def network_dns_request(
	domain: str = Query(..., min_length=1, max_length=253),
	record_type: str = Query("A", min_length=1, max_length=20),
	nameserver: str = Query("1.1.1.1", min_length=1, max_length=100),
) -> dict[str, Any]:
	return mnetwork.dns_request(domain=domain, type=record_type, nameserver=nameserver)


@router.get("/network/dns/reverse", tags=["Network"])
def network_reverse_dns(
	ip: str = Query(..., min_length=1, max_length=100),
	nameserver: str = Query("1.1.1.1", min_length=1, max_length=100),
) -> dict[str, Any]:
	return mnetwork.reverse_dns(ip=ip, nameserver=nameserver)


@router.get("/network/subnet_mask_to_cidr", tags=["Network"])
def network_subnet_mask_to_cidr(subnet_mask: str = Query(..., min_length=7, max_length=15)) -> dict[str, Any]:
	return mnetwork.subnet_mask_to_cidr(subnet_mask=subnet_mask)


@router.get("/network/cidr_to_subnet_mask", tags=["Network"])
def network_cidr_to_subnet_mask(cidr: int = Query(..., ge=0, le=32)) -> dict[str, Any]:
	return mnetwork.cidr_to_subnet_mask(cidr=cidr)


@router.get("/network/ip_range", tags=["Network"])
def network_ip_range(cidr: str = Query(..., min_length=1, max_length=50)) -> dict[str, Any]:
	return mnetwork.ip_range(cidr=cidr)


@router.get("/network/ip_range/recommended", tags=["Network"])
def network_recommended_ip_ranges(
	network_type: str = Query("private", min_length=1, max_length=50),
	devices: int = Query(254, ge=1),
	range_id: int = Query(1, ge=0),
) -> dict[str, Any]:
	return mnetwork.recommended_ip_ranges(type=network_type, devices=devices, id=range_id)
