// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ATFA evidence anchor
/// @notice Anchors the digest of every ATFA authorisation decision (device report hash, trust,
///         anomaly score, exposure, risk, decision, policy version) before settlement.
///         A settlement service releases payment only for digests anchored with decision APPROVE.
contract ATFAEvidenceAnchor {
    uint8 public constant APPROVE = 0;
    uint8 public constant HOLD = 1;
    uint8 public constant REJECT = 2;

    struct Anchor {
        uint64 anchoredAt;   // block timestamp; 0 = not anchored
        uint8 decision;
    }

    address public admin;
    mapping(address => bool) public authorisers;
    mapping(bytes32 => Anchor) public anchors;
    uint256 public anchoredCount;

    event AuthoriserSet(address indexed who, bool allowed);
    event Anchored(bytes32 indexed digest, bytes32 indexed deviceId, uint64 day, uint8 decision);
    event BatchAnchored(uint256 count, uint256 firstIndex);

    modifier onlyAdmin() {
        require(msg.sender == admin, "not admin");
        _;
    }

    modifier onlyAuthoriser() {
        require(authorisers[msg.sender], "not authoriser");
        _;
    }

    /// @param admin_ governance wallet; the deployer (the ATFA engine key) becomes an authoriser.
    constructor(address admin_) {
        admin = admin_;
        authorisers[msg.sender] = true;
        emit AuthoriserSet(msg.sender, true);
    }

    function setAuthoriser(address who, bool allowed) external onlyAdmin {
        authorisers[who] = allowed;
        emit AuthoriserSet(who, allowed);
    }

    function anchor(bytes32 digest, bytes32 deviceId, uint64 day, uint8 decision) external onlyAuthoriser {
        require(decision <= REJECT, "bad decision");
        require(anchors[digest].anchoredAt == 0, "already anchored");
        anchors[digest] = Anchor(uint64(block.timestamp), decision);
        unchecked { anchoredCount++; }
        emit Anchored(digest, deviceId, day, decision);
    }

    function anchorBatch(bytes32[] calldata digests, uint8[] calldata decisions) external onlyAuthoriser {
        require(digests.length == decisions.length, "length mismatch");
        uint256 first = anchoredCount;
        for (uint256 i = 0; i < digests.length; i++) {
            require(decisions[i] <= REJECT, "bad decision");
            require(anchors[digests[i]].anchoredAt == 0, "already anchored");
            anchors[digests[i]] = Anchor(uint64(block.timestamp), decisions[i]);
        }
        unchecked { anchoredCount += digests.length; }
        emit BatchAnchored(digests.length, first);
    }

    /// @notice Pre-settlement check: true only for an anchored APPROVE decision.
    function isSettleable(bytes32 digest) external view returns (bool) {
        Anchor memory a = anchors[digest];
        return a.anchoredAt != 0 && a.decision == APPROVE;
    }
}
